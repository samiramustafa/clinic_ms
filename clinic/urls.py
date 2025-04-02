from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
from rest_framework.routers import DefaultRouter
# from .views import CustomTokenObtainPairView
# from rest_framework_simplejwt.views import TokenRefreshView
from .views import AppointmentDetailView, AppointmentListCreateView, AvailableTimeDetailView, AvailableTimeListCreateView, DoctorViewSet, FeedbackDetailView, FeedbackListCreateView, PatientViewSet, UserViewSet



router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'patients', PatientViewSet)
router.register(r'doctors', DoctorViewSet)
router.register(r'cities', CityViewSet)

urlpatterns = [

    path('', include(router.urls)),
    path('login/', login_view, name='login'),
    path("api/cities/", CityViewSet.as_view({"get": "list"}), name="cities-list"),
    path("api/areas/", AreaListView.as_view(), name="area-list"),
    path('api/', include(router.urls)),
    path('api/users/me/', UserViewSet.as_view({'get': 'me', 'put': 'me'}), name='user-me'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # ✅ تسجيل الدخول
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # ✅ تحديث التوكن
    path("available-times/", AvailableTimeListCreateView.as_view(), name="available_times_list"),
    path("available-times/<int:pk>/", AvailableTimeDetailView.as_view(), name="available_times_details"),
    path("appointments/", AppointmentListCreateView.as_view(), name="appointments_list"),
    path("appointments/<int:pk>/", AppointmentDetailView.as_view(), name="appointment_detail"),
    path("feedbacks/", FeedbackListCreateView.as_view(), name="feedback-list-create"),
    path("feedbacks/<int:pk>/", FeedbackDetailView.as_view(), name="feedback-detail"),
    

]

    
