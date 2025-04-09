# clinic/apps.py
from django.apps import AppConfig

class ClinicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic' # تأكد أن هذا اسم التطبيق الصحيح

    def ready(self):
        import clinic.signals # استيراد ملف الـ signals لتسجيلها