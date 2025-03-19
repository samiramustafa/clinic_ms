from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('clinic.urls')),  # تأكد من أن هذا السطر موجود
]
