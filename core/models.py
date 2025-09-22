from django.db import models

# Create your models here.


class DailyCongressRecord(models.Model):
    issue_date = models.DateField(unique=True)
    summary = models.TextField(blank=True, null=True)
    pdf_url = models.URLField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"Congressional Record for {self.issue_date}"

    class Meta:
        verbose_name = "Daily Congressional Record"
        verbose_name_plural = "Daily Congressional Records"