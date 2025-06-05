import requests
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from congress.models import Congress, Member, Membership
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import time

load_dotenv()

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"
MAX_THREADS = 10  # Adjust based on available resources
REQUESTS_PER_HOUR = 5000
SECONDS_BETWEEN_REQUESTS = 3600 / REQUESTS_PER_HOUR


class Command(BaseCommand):
    help = "Fetches members of Congress and saves them to the database."

    def handle(self, *args, **kwargs):
        self.stdout.write("Fetching members from Congress.gov API...")
        members_data = fetch_members()

        if members_data:
            save_members(members_data)
        else:
            self.stdout.write(self.style.ERROR("No data received."))


def throttled_get(url):
    while True:
        response = requests.get(url)

        remaining = response.headers.get("x-ratelimit-remaining")
        retry_after = response.headers.get("retry-after")

        # Handle rate limiting
        if int(remaining) % 1000 == 0:
            print(f"📊 Remaining requests: {remaining or 'unknown'}")
        if remaining == "0":
            wait_time = int(retry_after or 60)
            print(f"🚦 Rate limit hit. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            continue

        # # For debugging/logging
        # remaining_num = int(remaining) if remaining else None
        # if remaining_num % 500 == 0:
        #     print(f"📊 Remaining requests: {remaining or 'unknown'}")

        # # Throttle between requests (proactive spacing)
        # time.sleep(SECONDS_BETWEEN_REQUESTS)
        return response


def fetch_members():
    members = []
    offset = 0

    while True:
        url = f"{BASE_URL}/member?api_key={API_KEY}&offset={offset}&limit=250"
        response = throttled_get(url)

        if response.status_code != 200:
            print(f"❌ Error fetching data: {response.status_code}")
            break

        data = response.json()
        pagination_info = data.get("pagination", {})
        next_page = pagination_info.get("next", None)

        if "members" in data:
            members.extend(data["members"])
            print(f"Fetched {len(members)} members from page {offset//20 + 1}.")

        else:
            print("❌ No members found in response.")
            break

        if next_page:
            offset += 250
        else:
            print(f"No next page. Ending fetch.")
            break

    print(f"Total members fetched: {len(members)}")
    return members


def save_members(members_data):
    """Saves member data to the database with multithreading for fetching details."""
    members_to_process = []

    for member in members_data:
        bioguide_id = member.get("bioguideId")
        name = member.get("name")
        image_url = member.get("depiction", {}).get("imageUrl", "No Image URL Provided")
        image_attribution = member.get("depiction", {}).get(
            "attribution", "No Attribution Provided"
        )
        state = member.get("state")

        member_obj, _ = Member.objects.update_or_create(
            bioguide_id=bioguide_id,
            defaults={
                "name": name,
                "image_url": image_url,
                "image_attribution": image_attribution,
                "last_updated": datetime.now(),
                "state": state,
            },
        )

        if not member_obj.fully_processed:
            members_to_process.append((bioguide_id, member_obj))
        print(len(members_to_process), "members to process.")
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_member = {
            executor.submit(fetch_all_member_data, m_id): (m_id, m_obj)
            for m_id, m_obj in members_to_process
        }

        for future in as_completed(future_to_member):
            bioguide_id, member_obj = future_to_member[future]
            try:
                result = future.result()
                if result and result["details"]:
                    save_memberships(
                        member_obj,
                        result["details"],
                        result["sponsored_legislation"],
                        result["cosponsored_legislation"],
                    )
                    member_obj.fully_processed = True
                    member_obj.save()
                    print(
                        f"✅ Successfully processed {member_obj.name} ({bioguide_id})"
                    )
            except Exception as e:
                print(f"❌ Error processing {member_obj.name} ({bioguide_id}): {e}")


def fetch_member_details(bioguide_id):
    """Fetches details about a single member, including terms and leadership."""

    while True:
        url = f"{BASE_URL}/member/{bioguide_id}?api_key={API_KEY}"
        response = throttled_get(url)

        if response.status_code == 200:
            return response.json().get("member", {})
        else:
            print(f"Response: {response.json()}")
            print(
                f"Error fetching member details for {bioguide_id}: {response.status_code}"
            )
            return None


def fetch_sponsored_legislation(bioguide_id):
    """Fetches sponsored legislation for a member."""
    counts_by_congress = defaultdict(int)
    offset = 0

    while True:
        url = f"{BASE_URL}/member/{bioguide_id}/sponsored-legislation?offset={offset}&limit=250&api_key={API_KEY}"
        response = throttled_get(url)
        if response.status_code == 200:
            data = response.json()
            pagination_info = data.get("pagination", {})
            next_page = pagination_info.get("next", None)
            for item in data.get("sponsoredLegislation", []):
                congress_number = item.get("congress")
                if congress_number:
                    counts_by_congress[congress_number] += 1
            if next_page:
                offset += 250
            else:
                break
        else:
            print(
                f"Error fetching sponsored legislation for {bioguide_id}: {response.status_code}"
            )
            break
    print(f"Sponsored legislation counts for {bioguide_id}: {counts_by_congress}")
    return counts_by_congress


def fetch_cosponsored_legislation(bioguide_id):
    counts_by_congress = defaultdict(int)
    offset = 0

    while True:
        url = f"{BASE_URL}/member/{bioguide_id}/cosponsored-legislation?offset={offset}&limit=250&api_key={API_KEY}"
        response = throttled_get(url)
        if response.status_code == 200:
            data = response.json()
            pagination_info = data.get("pagination", {})
            next_page = pagination_info.get("next", None)
            for item in data.get("cosponsoredLegislation", []):
                congress_number = item.get("congress")
                if congress_number:
                    counts_by_congress[congress_number] += 1
            if next_page:
                offset += 250
            else:
                break
        else:
            print(
                f"Error fetching cosponsored legislation for {bioguide_id}: {response.status_code}"
            )
            break
    print(f"Cosponsored legislation counts for {bioguide_id}: {counts_by_congress}")
    return counts_by_congress


def save_memberships(
    member, member_data, sponsored_legislation, cosponsored_legislation
):
    """Saves membership history for a given member.
    Creates multiple entries for different terms."""

    # First handle leadership roles
    for leadership_role in member_data.get("leadership", []):
        role = leadership_role.get("type")
        congress_number = leadership_role.get("congress")

        # Find the corresponding membership and update its leadership role
        try:
            membership = Membership.objects.get(
                member=member, congress__congress_number=congress_number
            )
            membership.leadership_role = role
            membership.save()
        except Membership.DoesNotExist:
            print(
                f"No membership found for {member.name} in Congress {congress_number}"
            )

    for term in member_data.get("terms", []):
        congress_number = term.get("congress")
        chamber = term.get("chamber")
        start_year = term.get("startYear")
        end_year = term.get("endYear", None)
        district = (
            term.get("district", None)
            if chamber == "House of Representatives"
            else None
        )

        # Ensure Congress exists
        try:
            congress = Congress.objects.get(congress_number=congress_number)
        except Congress.DoesNotExist:
            print(f"❌ Congress {congress_number} not found in DB. Skipping term.")
            continue

        # Determine party at the time
        party_history = member_data.get("partyHistory", [])
        party = next(
            (p["partyName"] for p in party_history if p["startYear"] <= start_year),
            "Unknown",
        )
        print(
            f"Saving membership for {member.name} in Congress {congress_number} with {sponsored_legislation.get(congress_number, 0)} sponsored bills."
        )

        # Create or update Membership record
        Membership.objects.update_or_create(
            member=member,
            congress=congress,
            defaults={
                "chamber": chamber,
                "party": party,
                "district": district,
                "start_year": start_year,
                "end_year": end_year,
                "sponsored_legislation_count": sponsored_legislation.get(
                    congress_number, 0
                ),
                "cosponsored_legislation_count": cosponsored_legislation.get(
                    congress_number, 0
                ),
            },
        )


def fetch_all_member_data(bioguide_id):
    details = fetch_member_details(bioguide_id)
    if not details:
        return None
    sponsored_legislation = fetch_sponsored_legislation(bioguide_id)
    cosponsored_legislation = fetch_cosponsored_legislation(bioguide_id)

    return {
        "details": details,
        "sponsored_legislation": sponsored_legislation,
        "cosponsored_legislation": cosponsored_legislation,
    }
