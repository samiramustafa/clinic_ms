# Generated by Django 5.1.7 on 2025-03-17 12:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='available_time',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='clinic.availabletime'),
        ),
    ]
