# from congress.models import Member
# from django.core.management.base import BaseCommand


# class Command(BaseCommand):
#     help = "Flags members as fully processed if they have non-zero sponsored and cosponsored legislation counts."

#     def handle(self, *args, **kwargs):
#         members_to_flag = flag_members()
#         self.stdout.write(
#             f"✅ Flagged {members_to_flag} members as fully processed."
#         )


# def flag_members():
#     # Get all members who have at least one membership with non-zero sponsored and cosponsored counts
#     members_to_flag = Member.objects.filter(
#         membership__sponsored_legislation_count__gt=0,
#         membership__cosponsored_legislation_count__gt=0,
#     ).distinct()

#     count = members_to_flag.count()

#     # Set the flag
#     for member in members_to_flag:
#         member.fully_processed = True
#         member.save()

#     return count
from congress.models import Member
from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):
    help = "Unflags members if they have any memberships with 0 sponsored OR 0 cosponsored legislation."

    def handle(self, *args, **kwargs):
        count = unflag_incomplete_members()
        self.stdout.write(
            f"✅ Set fully_processed = False for {count} members."
        )


def unflag_incomplete_members():
    # Find members with any membership where either count is 0
    members_to_unflag = Member.objects.filter(
        Q(membership__sponsored_legislation_count=0) |
        Q(membership__cosponsored_legislation_count=0)
    ).distinct()

    count = members_to_unflag.count()

    for member in members_to_unflag:
        member.fully_processed = False
        member.save()

    return count

