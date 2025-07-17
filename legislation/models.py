from django.db import models
from django.contrib.postgres.fields import ArrayField
from congress.models import Congress


# Create your models here.


class Bills(models.Model):
    """Model for storing bills information."""
    id = models.AutoField(primary_key=True)
    congress = models.ForeignKey(Congress, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=500, null=True)
    type = models.CharField(max_length=3, null=True)
    latest_action_date = models.DateField(null=True)
    latest_action = models.CharField(max_length=100, null=True)
    origin_chamber = models.CharField(max_length=10, null=True)
    url = models.URLField(max_length=150, null=True)
    full_text_url = models.URLField(max_length=150, null=True)
    gemini_summary= models.CharField(max_length=1000, null=True)
    tags= ArrayField( models.CharField(max_length=25, blank=True), size=3, null=True)

    def __str__(self):
        return "Bills"
