# Generated by Django 5.1.7 on 2025-03-20 00:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0005_doctor_clinicaddress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctor',
            name='fees',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0.01)]),
        ),
    ]
