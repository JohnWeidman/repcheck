import requests
import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from congress.models import Congress, Member, Membership
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

load_dotenv()

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"
MAX_THREADS = 10  # Adjust based on available resources


class Command(BaseCommand):
    help = "Fetches members of Congress and saves them to the database."

    def handle(self, *args, **kwargs):
        self.stdout.write("Fetching members from Congress.gov API...")
        members_data = fetch_members()

        if members_data:
            save_members(members_data)
        else:
            self.stdout.write(self.style.ERROR("No data received."))


def fetch_members():
    """Fetches the list of members from the API using pagination."""
    members = []
    offset = 0

    while True:
        url = f"{BASE_URL}/member?api_key={API_KEY}&offset={offset}"
        response = requests.get(url) 

        if response.status_code != 200:
            tqdm.write(f"❌ Error fetching data: {response.status_code}")
            break

        data = response.json()
        pagination_info = data.get("pagination", {})
        next_page = pagination_info.get("next", None)

        if "members" in data:
            members.extend(data["members"])
            tqdm.write(f"Fetched {len(members)} members from page {offset//20 + 1}.")
            
        else:
            tqdm.write("❌ No members found in response.")
            break
        
        if next_page:
            offset += 20
        else:
            tqdm.write(f"No next page. Ending fetch.")
            break
    
    tqdm.write(f"Total members fetched: {len(members)}")
    return members

def save_members(members_data):
    """Saves member data to the database with multithreading for fetching details."""
    members_to_process = []

    for member in members_data:
        bioguide_id = member.get("bioguideId") 
        name = member.get("name")
        image_url = member.get("depiction" , {}).get("imageUrl", "No Image URL Provided")
        image_attribution = member.get("depiction" , {}).get("attribution", "No Attribution Provided")
        state = member.get("state")

        member_obj, _ = Member.objects.update_or_create(
            bioguide_id=bioguide_id,
            defaults={
                "name": name,
                "image_url": image_url,
                "image_attribution": image_attribution,
                "last_updated": datetime.now(),
                "state": state,
            }
        )

        members_to_process.append((bioguide_id, member_obj))

    # Fetch member details in parallel
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_member = {executor.submit(fetch_member_details, m_id): (m_id, m_obj) for m_id, m_obj in members_to_process}

        for future in as_completed(future_to_member):
            bioguide_id, member_obj = future_to_member[future]
            try:
                member_details = future.result()
                if member_details:
                    print(f"Member details {member_details} fetched for {bioguide_id}")
                    save_memberships(member_obj, member_details)
                    print(f"Saved Member {bioguide_id} ({member_obj.name})")
            except Exception as e:
                print(f"Error processing member {bioguide_id}: {e}")

"""Not saving memberships in congresses that are not in the database"""

def fetch_member_details(bioguide_id):
    """Fetches details about a single member, including terms and leadership."""
    url = f"{BASE_URL}/member/{bioguide_id}?api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get("member", {})
    else:
        print(f"Response: {response.json()}")
        print(f"Error fetching member details for {bioguide_id}: {response.status_code}")
        return None


def save_memberships(member, member_data):
    """Saves membership history for a given member. 
       Creates multiple entries for different terms."""
    
    for term in member_data.get("terms", []):
        congress_number = term.get("congress")
        chamber = term.get("chamber")
        start_year = term.get("startYear")
        end_year = term.get("endYear", None)
        state_code = term.get("stateCode", "")
        district = term.get("district", None) if chamber == "House" else None


        # Ensure Congress exists
        congress, _ = Congress.objects.get_or_create(congress_number=congress_number)

        # Determine party at the time
        party_history = member_data.get("partyHistory", [])
        party = next((p["partyName"] for p in party_history if p["startYear"] <= start_year), "Unknown")

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
            }
        )
