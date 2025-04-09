from django.apps import AppConfig

class ClinicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic'  # Must be just 'clinic' (no dots)