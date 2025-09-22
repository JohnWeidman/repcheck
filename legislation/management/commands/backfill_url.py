from django.core.management.base import BaseCommand
from legislation.models import Bills


class Command(BaseCommand):
    help = "Update bill URLs using existing data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )

    def handle(self, *args, **options):
        # Get bills that either have no URL or have the old URL format
        bills_to_update = Bills.objects.filter(url__startswith="api")

        total_count = bills_to_update.count()
        self.stdout.write(f"Found {total_count} bills to update")

        if total_count == 0:
            self.stdout.write("No bills need URL updates!")
            return

        updated_count = 0

        for bill in bills_to_update:
            # Construct the new URL using existing data
            new_url = f"https://api.congress.gov/v3/bill/{bill.congress.congress_number}/{bill.type}/{bill.number}"

            if options["dry_run"]:
                self.stdout.write(f"Would update bill {bill.number}: {new_url}")
            else:
                bill.url = new_url
                bill.save(update_fields=["url"])
                updated_count += 1
                self.stdout.write(f"Updated bill {bill.number}: {new_url}")

        if not options["dry_run"]:
            self.stdout.write(f"Successfully updated {updated_count} bills with URLs")
        else:
            self.stdout.write(
                f"Dry run complete - {total_count} bills would be updated"
            )
