from django.db import models
from django.contrib.postgres.fields import ArrayField
from congress.models import Congress


# Create your models here.


class Bills(models.Model):
    """Model for storing bills information."""
    summary= models.CharField(max_length=1000)
    tags= ArrayField( models.CharField(max_length=15, blank=True), size=5)

    def __str__(self):
        return "Bills"
