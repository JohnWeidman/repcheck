import yaml
from django.core.management.base import BaseCommand
import os
from congress.models import Member


class Command(BaseCommand):

    help = "Fetches historical legislators data from YAML file."

    def handle(self, *args, **kwargs):
        main_path = "data/congress-legislators/legislators-historical.yaml"
        full_path = os.path.abspath(main_path)
        print(f"Looking for YAML at: {full_path}")
        try:
            with open(main_path, "r") as f:
                legislators = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print("Error loading YAML:", e)
        except FileNotFoundError:
            print(f"File not found: {main_path}")
            return
        except Exception as e:
            print(f"An error occurred: {e}")
            return
        for legislator in legislators:
            # Extract bioguide_id from legislator data
            bioguide_id = legislator.get("id", {}).get("bioguide", "")

            # Check if member already exists
            if not Member.objects.filter(bioguide_id=bioguide_id).exists():
                first_name = legislator.get("name", {}).get("first", "")
                last_name = legislator.get("name", {}).get("last", "")

                name = ", ".join([last_name, first_name])
                # Create new member
                Member.objects.create(
                    name=name,
                    bioguide_id=bioguide_id,
                    state=legislator.get("terms", [{}])[-1].get("state", ""),
                )
