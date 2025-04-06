# from django.urls import include, path
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from .views import *
# from rest_framework.routers import DefaultRouter
# from .views import login_view


# router = DefaultRouter()
# router.register(r'users', UserViewSet, basename='user')
# router.register(r'patients', PatientViewSet)
# router.register(r'doctors', DoctorViewSet)
# router.register(r'cities', CityViewSet)

# urlpatterns = [
#     path('', include(router.urls)),
#     # path('login/', login_view, name='login'),
#     path("api/cities/", CityViewSet.as_view({"get": "list"}), name="cities-list"),
#     path("api/areas/", AreaListView.as_view(), name="area-list"),
#     path('api/', include(router.urls)),
#     path('api/users/me/', UserViewSet.as_view({'get': 'me', 'put': 'me'}), name='user-me'),
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), 
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
#     path("available-times/", AvailableTimeListCreateView.as_view(), name="available_times_list"),
#     path("available-times/<int:pk>/", AvailableTimeDetailView.as_view(), name="available_times_details"),
#     path("appointments/", AppointmentListCreateView.as_view(), name="appointments_list"),
#     path("appointments/<int:pk>/", AppointmentDetailView.as_view(), name="appointment_detail"),
#     path("feedbacks/", FeedbackListCreateView.as_view(), name="feedback-list-create"),
#     path("feedbacks/<int:pk>/", FeedbackDetailView.as_view(), name="feedback-detail"),
#     path('api/admin/login/', AdminTokenObtainPairView.as_view(), name='admin_token_obtain_pair'),

#     path('api/admin/feedbacks/', AdminFeedbackListView.as_view(), name='admin_feedback_list'),

#     path('api/admin/feedbacks/<int:pk>/', AdminFeedbackDetailView.as_view(), name='admin_feedback_detail'),

# ]


# In clinic/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserViewSet, PatientViewSet, DoctorViewSet, CityViewSet, AreaListView,
    AdminTokenObtainPairView, AdminFeedbackListView, AdminFeedbackDetailView,
    AvailableTimeListCreateView, AvailableTimeDetailView,
    AppointmentListCreateView, AppointmentDetailView,
    FeedbackListCreateView, FeedbackDetailView,
    # لا حاجة لاستيراد login_view إذا لم تكن مستخدمة
)

# --- تعريف الـ Router ---
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'patients', PatientViewSet, basename='patient') # استخدم basename لتجنب مشاكل اسم الـ URL
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'cities', CityViewSet, basename='city')
# لا نسجل AreaListView هنا لأنها ListAPIView وليست ViewSet

# --- تعريف الـ urlpatterns ---
urlpatterns = [
    # --- 1. تضمين مسارات الـ router أولاً (ستكون تحت /api/ بسبب الملف الرئيسي) ---
    # مثال: /api/users/, /api/users/me/, /api/doctors/, /api/patients/, /api/cities/
    path('', include(router.urls)),

    # --- 2. مسارات API Tokens (تحت /api/) ---
    # /api/token/, /api/token/refresh/
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- 3. مسارات الأدمن (تحت /api/) ---
    # /api/admin/login/, /api/admin/feedbacks/, /api/admin/feedbacks/{pk}/
    path('admin/login/', AdminTokenObtainPairView.as_view(), name='admin_token_obtain_pair'),
    path('admin/feedbacks/', AdminFeedbackListView.as_view(), name='admin_feedback_list'),
    path('admin/feedbacks/<int:pk>/', AdminFeedbackDetailView.as_view(), name='admin_feedback_detail'),

    # --- 4. مسارات أخرى خاصة بـ clinic (تحت /api/) ---
    # /api/areas/
    path("areas/", AreaListView.as_view(), name="area-list"),

    # /api/available-times/, /api/available-times/{pk}/
    path("available-times/", AvailableTimeListCreateView.as_view(), name="available_times_list"),
    path("available-times/<int:pk>/", AvailableTimeDetailView.as_view(), name="available_times_details"),

    # /api/appointments/, /api/appointments/{pk}/
    path("appointments/", AppointmentListCreateView.as_view(), name="appointments_list"),
    path("appointments/<int:pk>/", AppointmentDetailView.as_view(), name="appointment_detail"),

    # /api/feedbacks/, /api/feedbacks/{pk}/ (المسارات العامة للتقييمات)
    path("feedbacks/", FeedbackListCreateView.as_view(), name="feedback-list-create"),
    path("feedbacks/<int:pk>/", FeedbackDetailView.as_view(), name="feedback-detail"),

    # --- مسارات مكررة أو غير ضرورية (تمت إزالتها) ---
    # path('api/cities/', CityViewSet.as_view({"get": "list"}), name="cities-list"), # مغطى بالـ router
    # path('api/', include(router.urls)), # مكرر
    # path('api/users/me/', UserViewSet.as_view({'get': 'me', 'put': 'me'}), name='user-me'), # مغطى بالـ router
]
