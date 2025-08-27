# myapp/migrations/000x_create_pg_trgm.py
from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension

class Migration(migrations.Migration):

    dependencies = [
        ('congress', '0009_member_fully_processed'),  # Adjust this to your last migration
    ]

    operations = [
        TrigramExtension(),
    ]