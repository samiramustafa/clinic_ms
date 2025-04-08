from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from django.db.models.signals import post_save

from .models import CustomUser, Patient, Doctor

User = get_user_model()

@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    if sender.name == "clinic":  # تأكد من أن الإشارة تعمل فقط مع تطبيقك
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='admin',
                full_name='Admin User'  # تأكد من أن الاسم يحتوي على كلمتين
            )




