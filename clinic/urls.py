from django.urls import include, path
# from.views import UserDetailView, UserListCreateView
from rest_framework.routers import DefaultRouter
# from .views import CustomTokenObtainPairView
# from rest_framework_simplejwt.views import TokenRefreshView
from .views import AppointmentDetailView, AppointmentListCreateView, AvailableTimeDetailView, AvailableTimeListCreateView, DoctorViewSet, FeedbackDetailView, FeedbackListCreateView, PatientViewSet, UserViewSet



router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'doctors', DoctorViewSet)

urlpatterns = [

    path('', include(router.urls)),
    # path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),



    # path("users/", UserListCreateAPIView.as_view(), name="user-list-create"),
    # path("users/<int:pk>/", UserDetailAPIView.as_view(), name="user-detail"),
    path("available-times/", AvailableTimeListCreateView.as_view(), name="available_times_list"),
    path("available-times/<int:pk>/", AvailableTimeDetailView.as_view(), name="available_times_details"),
    path("appointments/", AppointmentListCreateView.as_view(), name="appointments_list"),
    path("appointments/<int:pk>/", AppointmentDetailView.as_view(), name="appointment_detail"),
    path("feedbacks/", FeedbackListCreateView.as_view(), name="feedback-list-create"),
    path("feedbacks/<int:pk>/", FeedbackDetailView.as_view(), name="feedback-detail"),
    

]

    