from django.core.management.base import BaseCommand
from clinic.models import NewsletterSubscriber
from django.conf import settings

class Command(BaseCommand):
    help = 'Simulate sending newsletter emails'

    def handle(self, *args, **options):
        if settings.SIMULATED_EMAILS['ENABLED']:
            subscribers = NewsletterSubscriber.objects.filter(is_active=True)
            for sub in subscribers:
                sub.send_welcome_email()
            self.stdout.write(f"Simulated emails sent to {subscribers.count()} subscribers")