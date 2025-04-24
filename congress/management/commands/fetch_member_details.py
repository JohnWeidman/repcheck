import yaml
from django.core.management.base import BaseCommand
import os
from congress.models import Member, MemberDetails


class Command(BaseCommand):

    help = "Fetches historical legislators data from YAML file."

    def handle(self, *args, **kwargs):
        main_path = "data/congress-legislators/legislators-current.yaml"
        full_path = os.path.abspath(main_path)
        print(f"Looking for YAML at: {full_path}")

        social_path = "data/congress-legislators/legislators-social-media.yaml"
        full_social_path = os.path.abspath(social_path)
        print(f"Looking for social media YAML at: {full_social_path}")

        try:
            with open(main_path, "r") as f:
                legislators = yaml.safe_load(f)

            with open(social_path, "r") as f:
                social_data = yaml.safe_load(f)

        except yaml.YAMLError as e:
            print("Error loading YAML:", e)

        social_by_bioguide = {
            item["id"].get("bioguide"): item.get("social", {})
            for item in social_data
            if "id" in item
        }

        for legislator in legislators:
            bioguide_id = legislator["id"].get("bioguide")
            if not bioguide_id:
                self.stdout.write(
                    f"Skipping legislator without bioguide ID: {legislator}"
                )
                continue
            print(f"Processing legislator with bioguide ID: {bioguide_id}")
            try:
                member = Member.objects.get(bioguide_id=bioguide_id)
                print(f"Found member: {member.name}")

                social = social_by_bioguide.get(bioguide_id, {})
                if social:
                    print(f"Social Media: {social}")
                else:
                    print(f"No social media data found for {bioguide_id}")

            except Member.DoesNotExist:
                self.stdout.write(f"Member with bioguide ID {bioguide_id} not found.")
                continue
            print(legislator.get("terms", [{}])[-1].get("url", ""))
            birthday = legislator.get("bio", {}).get("birthday", {})
            website_url = legislator.get("terms", [{}])[-1].get("url", "")
            phone_number = legislator.get("terms", [{}])[-1].get("phone", "")
            open_secrets_id = legislator.get("id", {}).get("opensecrets", "")
            twitter_handle = social.get("twitter", "")
            facebook_handle = social.get("facebook", "")
            youtube_id = social.get("youtube", "")
            instagram_handle = social.get("instagram", "")
            try:
                member_details, created = MemberDetails.objects.update_or_create(
                    member=member,
                    defaults={
                        "birthday": birthday,
                        "website_url": website_url,
                        "phone_number": phone_number,
                        "open_secrets_id": open_secrets_id,
                        "twitter_handle": twitter_handle,
                        "facebook_handle": facebook_handle,
                        "youtube_id": youtube_id,
                        "instagram_handle": instagram_handle,
                    },
                )
                if created:
                    self.stdout.write(f"Created details for {member.name}")
                else:
                    self.stdout.write(f"Updated details for {member.name}")
            except Exception as e:
                self.stdout.write(f"Error saving details for {member.name}: {e}")
                continue


