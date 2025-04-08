import requests
import re
import os
from django.core.management.base import BaseCommand
from congress.models import Congress
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Ensure .env variables are loaded

API_KEY = os.getenv("CONGRESS_API_KEY")  # Getting API key from .env file
BASE_URL = "https://api.congress.gov/v3"  # Base URL for the Congress.gov API


def fetch_congress_list():
    """Fetches the list of Congresses from the API."""
    url = f"{BASE_URL}/congress?api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data: {response.status_code}, {response.text}")
        return None


def save_congresses(congress_data):
    for congress in congress_data.get("congresses", []):
        congress_name = congress.get("name", "").split()[0]

        # Extract the congress number as an integer
        congress_number_match = re.search(r"\d+", congress_name)
        if congress_number_match:
            congress_number = int(congress_number_match.group())  # Convert to integer
        else:
            continue  # Skip if no congress number is found

        start_year = congress.get("startYear")
        end_year = congress.get("endYear")

        if congress_number and start_year and end_year:
            # Create or update the Congress entry
            congress_obj, created = Congress.objects.update_or_create(
                congress_number=congress_number,
                defaults={
                    "start_date": datetime.strptime(
                        f"{start_year}-01-01", "%Y-%m-%d"
                    ).date(),
                    "end_date": datetime.strptime(
                        f"{end_year}-12-31", "%Y-%m-%d"
                    ).date(),
                },
            )

            print(f"Saved Congress {congress_number} ({start_year} - {end_year})")

            # Process the sessions for each Congress
            for session in congress.get("sessions", []):
                chamber = session.get("chamber")
                session_number = session.get("number")
                session_start_date = session.get("startDate")
                session_end_date = session.get("endDate")

                # Print session details for now (can be saved to the Membership model later)
                print(
                    f"Session {session_number} in {chamber}: {session_start_date} to {session_end_date}"
                )


class Command(BaseCommand):
    help = "Fetch and store Congress data from Congress.gov API"

    def handle(self, *args, **kwargs):
        data = fetch_congress_list()
        if data:
            save_congresses(data)
            self.stdout.write(self.style.SUCCESS("Congress data successfully updated!"))
        else:
            self.stderr.write(self.style.ERROR("Failed to fetch Congress data."))
