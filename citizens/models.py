from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Citizen(AbstractUser):
    """
    Custom user model for the application.
    Inherits from Django's AbstractUser to include all default fields.
    """
    REQUIRED_FIELDS = ['email']  # Ensure email is required
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='citizen_set',  # This fixes the conflict
        related_query_name='citizen',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='citizen_set',  # This fixes the conflict
        related_query_name='citizen',
    )
    
    congressional_district = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username  # or self.email, or any other field you prefer