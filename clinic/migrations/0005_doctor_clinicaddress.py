# Generated by Django 5.1.7 on 2025-03-19 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0004_doctor_average_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='clinicAddress',
            field=models.TextField(blank=True, null=True),
        ),
    ]
