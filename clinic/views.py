from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework import viewsets, generics
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .permissions import IsAdminRole
import time
from django.core.mail import send_mail
from django.conf import settings

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CustomUser operations.
    """
    queryset = CustomUser.objects.all()

    def get_serializer_class(self):
        if self.action == 'list' and self.request.user.is_authenticated and self.request.user.role == 'admin':
             return AdminUserSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if self.action == 'list':
            if user.is_authenticated and user.role == 'admin':
                return CustomUser.objects.all().order_by('-date_joined')
            else:
                return CustomUser.objects.none()
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'me']:
             if user.is_authenticated:
                  if self.action == 'me':
                      return CustomUser.objects.filter(pk=user.pk)
                  return CustomUser.objects.all()
        return CustomUser.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if instance == user:
            return Response({"detail": "Admins cannot delete their own account."}, status=status.HTTP_403_FORBIDDEN)
        if instance.is_superuser:
            return Response({"detail": "Superusers cannot be deleted."}, status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action in ['list', 'destroy', 'retrieve' ,'partial_update', 'update']:
            return [IsAdminRole()]
        elif self.action == 'create':
            return [AllowAny()]
        elif self.action == 'me':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        new_active_status = serializer.validated_data.get('is_active', instance.is_active)
        if 'is_active' in serializer.validated_data:
             if instance == user and not new_active_status:
                  raise serializers.ValidationError({"is_active": "Admins cannot deactivate their own account."})
             if instance.is_superuser and not new_active_status:
                  raise serializers.ValidationError({"is_active": "Superuser account cannot be deactivated."})
        serializer.save()

    @action(detail=False, methods=['get', 'put'], permission_classes=[IsAuthenticated], url_path='me')
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            user_data = serializer.data
            if user.role == 'patient':
                try:
                    patient_profile = user.patient_profile
                    patient_serializer = PatientSerializer(patient_profile)
                    user_data['patient_profile'] = patient_serializer.data
                except Patient.DoesNotExist:
                    user_data['patient_profile'] = None
            elif user.role == 'doctor':
                 try:
                    doctor_profile = user.doctor_profile
                    doctor_serializer = DoctorSerializer(doctor_profile)
                    user_data['doctor_profile'] = doctor_serializer.data
                 except Doctor.DoesNotExist:
                    user_data['doctor_profile'] = None
            return Response(user_data)

        elif request.method == 'PUT':
             user_serializer = self.get_serializer(user, data=request.data, partial=True)
             try:
                 user_serializer.is_valid(raise_exception=True)
             except serializers.ValidationError as e:
                  return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

             profile_serializer = None
             profile_data_key = None
             profile_errors = None
             profile_updated = False

             if user.role == 'patient':
                  profile_data_key = 'patient_profile'
                  if profile_data_key in request.data:
                     patient_data = request.data.get(profile_data_key)
                     if isinstance(patient_data, dict):
                         try:
                             patient_profile = user.patient_profile
                             profile_serializer = PatientSerializer(patient_profile, data=patient_data, partial=True)
                         except Patient.DoesNotExist:
                              profile_errors = {"detail": "Patient profile not found for this user."}
                     else:
                         profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}

             elif user.role == 'doctor':
                  profile_data_key = 'doctor_profile'
                  if profile_data_key in request.data:
                      doctor_data = request.data.get(profile_data_key)
                      if isinstance(doctor_data, dict):
                           try:
                               doctor_profile = user.doctor_profile
                               profile_serializer = DoctorSerializer(doctor_profile, data=doctor_data, partial=True)
                           except Doctor.DoesNotExist:
                                profile_errors = {"detail": "Doctor profile not found for this user."}
                      else:
                           profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}

             if profile_serializer:
                 try:
                     profile_serializer.is_valid(raise_exception=True)
                     profile_updated = True
                 except serializers.ValidationError as e:
                     profile_errors = e.detail

             if profile_errors:
                  return Response({f"{profile_data_key}_errors": profile_errors}, status=status.HTTP_400_BAD_REQUEST)
             else:
                  user_instance = user_serializer.save()

                  if profile_updated and profile_serializer:
                      profile_serializer.save()

                  final_serializer = self.get_serializer(user_instance)
                  final_response_data = final_serializer.data
                  if user.role == 'patient':
                     try: final_response_data['patient_profile'] = PatientSerializer(user_instance.patient_profile).data
                     except Patient.DoesNotExist: final_response_data['patient_profile'] = None
                  elif user.role == 'doctor':
                      try: final_response_data['doctor_profile'] = DoctorSerializer(user_instance.doctor_profile).data
                      except Doctor.DoesNotExist: final_response_data['doctor_profile'] = None

                  return Response(final_response_data)

class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [AllowAny]
    queryset = Doctor.objects.select_related(
        'user', 'user__city', 'user__area'
    ).all()

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    
class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    
class AreaListView(ListAPIView):
    serializer_class = AreaSerializer

    def get_queryset(self):
        city_id = self.request.GET.get("city")
        if city_id:
            return Area.objects.filter(city_id=city_id)
        return Area.objects.all()

@api_view(["POST"])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user:
        return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
    return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class AvailableTimeListCreateView(APIView):
    def get(self, request):
        doctor_id = request.query_params.get("doctor_id")
        if doctor_id:
            available_times = AvailableTime.objects.filter(doctor_id=doctor_id)
        else:
            available_times = AvailableTime.objects.all()

        serializer = AvailableTimeSerializer(available_times, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AvailableTimeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AvailableTimeDetailView(APIView):
    def get(self, request, pk):
        available_time = get_object_or_404(AvailableTime, pk=pk)
        serializer = AvailableTimeSerializer(available_time)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        available_time = get_object_or_404(AvailableTime, pk=pk)
        serializer = AvailableTimeSerializer(available_time, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        available_time = get_object_or_404(AvailableTime, pk=pk)
        available_time.delete()
        return Response({"message": "Available time deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class AppointmentListCreateView(APIView):
    def get(self, request):
        doctor_id = request.GET.get("doctor_id")
        if doctor_id:
            appointments = Appointment.objects.filter(doctor_id=doctor_id)
        else:
            appointments = Appointment.objects.all()

        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        doctor_id = request.data.get("doctor")
        available_time_id = request.data.get("available_time")

        available_time = get_object_or_404(AvailableTime, id=available_time_id)
        if available_time.doctor.id != int(doctor_id):
            return Response(
                {"error": "The selected available time does not belong to the chosen doctor."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppointmentDetailView(APIView):
    def get(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        serializer = AppointmentSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.delete()
        return Response({"message": "Appointment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class FeedbackListCreateView(APIView):
    def get(self, request):
        doctor_id = request.GET.get("doctor_id")
        if doctor_id:
            feedbacks = Feedback.objects.filter(doctor_id=doctor_id)
        else:
            feedbacks = Feedback.objects.all()

        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            serializer.instance.doctor.update_rating()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FeedbackDetailView(APIView):
    def get(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        serializer = FeedbackSerializer(feedback)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        serializer = FeedbackSerializer(feedback, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            serializer.instance.doctor.update_rating()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        doctor = feedback.doctor
        feedback.delete()
        doctor.update_rating()
        return Response({"message": "Feedback deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer
    permission_classes = [AllowAny]

class AdminFeedbackListView(generics.ListAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        queryset = Feedback.objects.select_related('patient__user', 'doctor__user').all().order_by('-created_at')
        is_active_filter = self.request.query_params.get('is_active')
        if is_active_filter is not None:
             if is_active_filter.lower() == 'true':
                 queryset = queryset.filter(is_active=True)
             elif is_active_filter.lower() == 'false':
                 queryset = queryset.filter(is_active=False)
        return queryset

class AdminFeedbackDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAdminRole]
    queryset = Feedback.objects.all()

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.doctor:
             instance.doctor.update_rating()

    def perform_destroy(self, instance):
        doctor = instance.doctor
        instance.delete()
        if doctor:
             doctor.update_rating()

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import NewsletterSubscriber
import time

class NewsletterSignupView(APIView):
    permission_classes = []  # Allow anyone to access
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email already exists
        if NewsletterSubscriber.objects.filter(email=email).exists():
            return Response(
                {"message": "This email is already subscribed."},
                status=status.HTTP_200_OK
            )
        
        # Create new subscriber
        subscriber = NewsletterSubscriber.objects.create(email=email)
        
        # Simulate email sending
        print(f"\n=== Simulated Email to {email} ===\n")
        print("Subject: Welcome to Our Clinic Newsletter!")
        print(f"Body: Thank you for subscribing, {email}!")
        print("We'll keep you updated with our latest news and health tips.")
        print("\n=== End of Simulation ===\n")
        
        time.sleep(1)  # Simulate processing delay
        
        return Response(
            {
                "message": "Thank you for subscribing! A welcome email has been sent.",
                "simulated_email": {
                    "to": email,
                    "subject": "Welcome to Our Clinic Newsletter",
                    "body": "Thank you for subscribing...",
                    "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            },
            status=status.HTTP_201_CREATED
        )
        
