from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.contrib import admin
from clinic.views import AreaListView



urlpatterns = [
    path('admin/', admin.site.urls),
<<<<<<< HEAD
    
    path('api/', include('clinic.urls')),
=======
    path('clinic/', include('clinic.urls')),
>>>>>>> 5003695a9733c2cca0145603836773b9db08941d
    # path('api-auth/', include('rest_framework.urls'))
    # path('api/areas/', AreaListView.as_view(), name='area-list'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
