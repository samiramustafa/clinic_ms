# Generated by Django 5.1.7 on 2025-04-04 00:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctor',
            name='card',
            field=models.CharField(blank=True, max_length=14, null=True, unique=True),
        ),
    ]
