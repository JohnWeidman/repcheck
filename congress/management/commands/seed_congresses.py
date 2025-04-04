from congress.models import Congress
from django.core.management.base import BaseCommand
from datetime import datetime


class Command(BaseCommand):
    help = "Seeds the Congress model with initial data."
    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding Congress model with initial data...")

        start_year = 1789
        current_year = datetime.now().year
        congress_number = 1 

        while start_year <= current_year:
            end_year = start_year + 2

            Congress.objects.update_or_create(
                congress_number=congress_number,
                defaults={
                    "start_date": datetime.strptime(f"{start_year}-01-03", "%Y-%m-%d").date(),
                    "end_date": datetime.strptime(f"{end_year}-01-03", "%Y-%m-%d").date(),
                }
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Congress {congress_number} ({start_year} - {end_year}) seeded successfully."
                )
            )
            start_year = end_year
            congress_number += 1
        self.stdout.write(self.style.SUCCESS("All Congress data seeded successfully!"))
