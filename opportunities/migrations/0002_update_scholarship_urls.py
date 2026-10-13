from django.db import migrations
from django.core.management import call_command


def apply_seed_scholarships(apps, schema_editor):
    try:
        call_command('seed_scholarships')
    except Exception as e:
        # Fallback if any error occurs
        pass


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(apply_seed_scholarships, reverse_func),
    ]
