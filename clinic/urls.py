from django.urls import include, path

# from.views import UserDetailView, UserListCreateView
from .views import AvailableTimeDetailView, AvailableTimeListCreateView, UserListCreateAPIView, UserDetailAPIView
from rest_framework.routers import DefaultRouter


urlpatterns = [
    # path("users/", UserListCreateView.as_view(), name="user-list-create"),  # عرض كل المستخدمين أو إضافة مستخدم جديد
    # path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
     path("users/", UserListCreateAPIView.as_view(), name="user-list-create"),
    path("users/<int:pk>/", UserDetailAPIView.as_view(), name="user-detail"),
    path("available-times/", AvailableTimeListCreateView.as_view(), name="available_times_list"),
    path("available-times/<int:pk>/", AvailableTimeDetailView.as_view(), name="available_times_details"),
    
]