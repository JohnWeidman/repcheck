from django.db import models

class Congress(models.Model):
    id = models.AutoField(primary_key=True)  # Auto incrementing primary key
    congress_number = models.IntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ['-congress_number']
        verbose_name_plural = "Congresses"

    def __str__(self):
        return f"Congress {self.congress_number} ({self.start_date} - {self.end_date})"

class Member(models.Model):
    id = models.AutoField(primary_key=True)  # Auto incrementing primary key
    bioguide_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=50)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    image_attribution = models.TextField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.state})"

class Membership(models.Model):
    id = models.AutoField(primary_key=True)  # Auto incrementing primary key
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    congress = models.ForeignKey(Congress, on_delete=models.CASCADE)
    chamber = models.CharField(max_length=10, choices=[("Senate", "Senate"), ("House", "House")])
    party = models.CharField(max_length=50)
    district = models.IntegerField(null=True, blank=True)  # House members only
    start_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('member', 'congress')  # Ensures a member is only listed once per Congress

    def __str__(self):
        return f"{self.member.name} ({self.chamber} - {self.party}, {self.congress})"
