from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Feedback)
admin.site.register(Appointment)
admin.site.register(AvailableTime)
admin.site.register(City) 
admin.site.register(Area)


from django.contrib import admin
from .models import NewsletterSubscriber, NewsletterLog

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active', 'email_count')
    list_filter = ('is_active',)
    search_fields = ('email',)

@admin.register(NewsletterLog)
class NewsletterLogAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'sent_at', 'email_type')
    readonly_fields = ('sent_at',)