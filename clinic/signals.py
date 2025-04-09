from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import NewsletterSubscriber

@receiver(post_save, sender=NewsletterSubscriber)
def send_welcome_email(sender, instance, created, **kwargs):
        if created and instance.is_active:
            instance.send_welcome_email()