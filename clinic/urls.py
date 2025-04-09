from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserViewSet, PatientViewSet, DoctorViewSet, CityViewSet, AreaListView,
    AdminTokenObtainPairView, AdminFeedbackListView, AdminFeedbackDetailView,
    AvailableTimeListCreateView, AvailableTimeDetailView,
    AppointmentListCreateView, AppointmentDetailView,
    FeedbackListCreateView, FeedbackDetailView,
    NewsletterSignupView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'cities', CityViewSet, basename='city')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/login/', AdminTokenObtainPairView.as_view(), name='admin_token_obtain_pair'),
    path('admin/feedbacks/', AdminFeedbackListView.as_view(), name='admin_feedback_list'),
    path('admin/feedbacks/<int:pk>/', AdminFeedbackDetailView.as_view(), name='admin_feedback_detail'),
    path("areas/", AreaListView.as_view(), name="area-list"),
    path("available-times/", AvailableTimeListCreateView.as_view(), name="available_times_list"),
    path("available-times/<int:pk>/", AvailableTimeDetailView.as_view(), name="available_times_details"),
    path("appointments/", AppointmentListCreateView.as_view(), name="appointments_list"),
    path("appointments/<int:pk>/", AppointmentDetailView.as_view(), name="appointment_detail"),
    path("feedbacks/", FeedbackListCreateView.as_view(), name="feedback-list-create"),
    path("feedbacks/<int:pk>/", FeedbackDetailView.as_view(), name="feedback-detail"),
    path("newsletter/signup/", NewsletterSignupView.as_view(), name="newsletter-signup"),
    # Removed the chat endpoint from he    ...existing patterns...,

]