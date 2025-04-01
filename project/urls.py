from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.contrib import admin
from clinic.views import AreaListView


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('clinic/', include('clinic.urls')),
    # path('api-auth/', include('rest_framework.urls'))
    path('api/areas/', AreaListView.as_view(), name='area-list'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
