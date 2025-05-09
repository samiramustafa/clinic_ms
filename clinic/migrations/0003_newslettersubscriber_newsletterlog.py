# Generated by Django 5.1.7 on 2025-04-08 19:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0002_feedback_admin_notes_feedback_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsletterSubscriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('subscribed_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_email_sent', models.DateTimeField(blank=True, null=True)),
                ('email_count', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='NewsletterLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('email_type', models.CharField(default='welcome', max_length=50)),
                ('simulated_content', models.TextField()),
                ('subscriber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='clinic.newslettersubscriber')),
            ],
            options={
                'ordering': ['-sent_at'],
            },
        ),
    ]
