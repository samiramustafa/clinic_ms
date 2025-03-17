from django.urls import path, include
from rest_framework.routers import DefaultRouter
from clinic.views import UserViewSet, PatientViewSet, DoctorViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'doctors', DoctorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
