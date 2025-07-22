from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime


class Congress(models.Model):
    id = models.AutoField(primary_key=True)
    congress_number = models.IntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-congress_number"]
        verbose_name_plural = "Congresses"
        
    @classmethod
    def get_current_congress_number(cls):
        current_date = datetime.now().date()
        congress_obj = cls.objects.filter(
            start_date__lte=current_date,
            end_date__gte=current_date
        ).first()
        return congress_obj.congress_number if congress_obj else None
    @classmethod
    def get_current_congress_object(cls):
        current_date = datetime.now().date()
        return cls.objects.filter(
            start_date__lte=current_date,
            end_date__gte=current_date
        ).first()
    def __str__(self):
        return f"Congress {self.congress_number} ({self.start_date} - {self.end_date})"


class Member(models.Model):
    id = models.AutoField(primary_key=True)
    bioguide_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=50)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    image_attribution = models.TextField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    fully_processed = models.BooleanField(default=False)

    def full_name(self):
        first = self.name.split(",")[1 if len(self.name.split(",")) > 1 else ""]
        last = self.name.split(",")[0] if "," in self.name else self.name
        return f"{first.strip()} {last.strip()}"

    def __str__(self):
        return f"{self.name} ({self.state})"


class Membership(models.Model):
    id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    congress = models.ForeignKey(Congress, on_delete=models.CASCADE)
    chamber = models.CharField(max_length=25)
    party = models.CharField(max_length=50)
    district = models.IntegerField(null=True, blank=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True)
    sponsored_legislation_count = models.IntegerField(default=0)
    cosponsored_legislation_count = models.IntegerField(default=0)
    leadership_role = models.CharField(max_length=50, null=True, blank=True)

    def is_current(self):
        return self.congress.congress_number in [119]  # TODO: Update with actual logic. Getting members that have died as current members

    class Meta:
        unique_together = (
            "member",
            "congress",
        )

    def __str__(self):
        return f"{self.member.name} ({self.chamber} - {self.party}, {self.congress})"


class MemberDetails(models.Model):
    id = models.AutoField(primary_key=True)
    member = models.OneToOneField(Member, on_delete=models.CASCADE)
    birthday = models.DateField(null=True, blank=True)
    website_url = models.URLField(null=True)
    phone_number = PhoneNumberField(null=True, blank=True)
    open_secrets_id = models.CharField(max_length=50, null=True, blank=True)
    twitter_handle = models.CharField(max_length=50, null=True, blank=True)
    facebook_handle = models.CharField(max_length=50, null=True, blank=True)
    youtube_id = models.CharField(max_length=50, null=True, blank=True)
    instagram_handle = models.CharField(max_length=50, null=True, blank=True)
    wikipedia = models.URLField(null=True, blank=True)

    def twitter_url(self):
        return (
            f"https://twitter.com/{self.twitter_handle}"
            if self.twitter_handle
            else None
        )

    def facebook_url(self):
        return (
            f"https://www.facebook.com/{self.facebook_handle}"
            if self.facebook_handle
            else None
        )

    def instagram_url(self):
        return (
            f"https://www.instagram.com/{self.instagram_handle}"
            if self.instagram_handle
            else None
        )

    def youtube_url(self):
        return f"https://www.youtube.com/{self.youtube_id}" if self.youtube_id else None

    def open_secrets_url(self):
        return (
            f"https://www.opensecrets.org/members-of-congress/summary?cid={self.open_secrets_id}"
            if self.open_secrets_id
            else None
        )

    def wikipedia_url(self):
        processed_wiki = self.wikipedia.replace(" ", "_") if self.wikipedia else None
        return (
            f"https://en.wikipedia.org/wiki/{processed_wiki}"
            if self.wikipedia
            else None
        )

    class Meta:
        verbose_name_plural = "Member Details"

    def __str__(self):
        return f"{self.member.name}"
