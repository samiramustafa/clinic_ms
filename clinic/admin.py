from django.contrib import admin
from .models import CustomUser,Patient ,Doctor ,Feedback, Appointment,AvailableTime
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Feedback)
admin.site.register(Appointment)
admin.site.register(AvailableTime)