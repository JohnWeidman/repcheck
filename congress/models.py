from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class Congress(models.Model):
    id = models.AutoField(primary_key=True)
    congress_number = models.IntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-congress_number"]
        verbose_name_plural = "Congresses"

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

    def __str__(self):
        return f"{self.name} ({self.state})"


class Membership(models.Model):
    id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    congress = models.ForeignKey(Congress, on_delete=models.CASCADE)
    chamber = models.CharField(
        max_length=25, choices=[("Senate", "Senate"), ("House", "House")]
    )
    party = models.CharField(max_length=50)
    district = models.IntegerField(null=True, blank=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True)
    # New field to track leadership roles?

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
    phone_number = PhoneNumberField( null=True, blank=True)
    open_secrets_id = models.CharField(max_length=50, null=True, blank=True)
    twitter_handle = models.CharField(max_length=50, null=True, blank=True)
    facebook_handle = models.CharField(max_length=50, null=True, blank=True)
    youtube_id = models.CharField(max_length=50, null=True, blank=True)
    instagram_handle = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Member Details"

    def __str__(self):
        return f"{self.member.name}"
