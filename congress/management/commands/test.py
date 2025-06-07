import requests
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from congress.models import Congress, Member, Membership
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

load_dotenv()

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"
MAX_THREADS = 10  # Adjust based on available resources
bioguide_id = "L000174"  # Example bioguide ID for testing


class Command(BaseCommand):
    help = "Fetches members of Congress and saves them to the database."

    def handle(self, *args, **kwargs):
        self.stdout.write("Fetching members from Congress.gov API...")
        leahy_data = fetch_sponsored_legislation(bioguide_id)
        print(f"Sponsored legislation for {bioguide_id}: {leahy_data}")


def fetch_sponsored_legislation(bioguide_id):
    """Fetches sponsored legislation for a member."""
    counts_by_congress = defaultdict(int)
    offset = 0

    while True:
        url = f"{BASE_URL}/member/{bioguide_id}/sponsored-legislation?offset={offset}&limit=250&api_key={API_KEY}"
        response = requests.get(url)
        # print(response.json())
        if response.status_code == 200:
            data = response.json()
            pagination_info = data.get("pagination", {})
            next_page = pagination_info.get("next", None)
            print(next_page)
            sponsored_leg = data.get("sponsoredLegislation", [])
            print(len(sponsored_leg))
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
    return counts_by_congress