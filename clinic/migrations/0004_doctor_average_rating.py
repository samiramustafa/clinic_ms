# Generated by Django 5.1.7 on 2025-03-17 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0003_alter_appointment_available_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='average_rating',
            field=models.FloatField(default=0.0),
        ),
    ]
