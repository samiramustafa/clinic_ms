from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework import viewsets,generics
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
from .permissions import IsAdminRole # استيراد الصلاحية المخصصة
# views.py

# ... (باقي الاستيرادات والكلاسات الأخرى مثل DoctorViewSet, PatientViewSet etc.)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet للتعامل مع المستخدمين (CustomUser).
    يتضمن إنشاء المستخدمين، وعرض/تعديل بيانات المستخدم المسجل (`/me`).
    """
    queryset = CustomUser.objects.all()
    #serializer_class = UserSerializer # Keep commented if using get_serializer_class

    # --- 👇 بداية الدوال على مستوى الكلاس ---
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
                      # Note: 'me' is detail=False, it doesn't use get_object/queryset filtering by pk.
                      # It operates directly on request.user. So returning all() is fine here too,
                      # or just filter by user.pk for consistency, but it won't affect 'me' action directly.
                      return CustomUser.objects.filter(pk=user.pk) # Let's keep this for safety if 'me' logic changes
                  # For other detail actions (retrieve, update, destroy)
                  return CustomUser.objects.all()
        # Fallback or for 'create' action etc.
        return CustomUser.objects.all()

    # --- 👇 الدوال الأخرى الآن على نفس مستوى get_queryset ---
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
            # 'me' action itself checks IsAuthenticated via decorator, but doesn't hurt to double check
            return [permissions.IsAuthenticated()]
        # Default permissions for any other potential actions
        return [permissions.IsAuthenticated()] # Or more restrictive if needed

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        new_active_status = serializer.validated_data.get('is_active', instance.is_active)
        # Use validated_data which is available after is_valid() call in update/partial_update
        # Check if the field was actually included in the request data for partial updates
        if 'is_active' in serializer.validated_data:
             if instance == user and not new_active_status:
                  raise serializers.ValidationError({"is_active": "Admins cannot deactivate their own account."})
             if instance.is_superuser and not new_active_status:
                  raise serializers.ValidationError({"is_active": "Superuser account cannot be deactivated."})
        serializer.save()

    @action(detail=False, methods=['get', 'put'], permission_classes=[IsAuthenticated], url_path='me')
    def me(self, request):
        user = request.user # The user making the request

        if request.method == 'GET':
            # Pass the authenticated user directly to the serializer
            serializer = self.get_serializer(user) # Use the correct serializer (UserSerializer)
            user_data = serializer.data
             # Add nested profile data
            if user.role == 'patient':
                try:
                    patient_profile = user.patient_profile
                    # Use the appropriate serializer for the profile
                    patient_serializer = PatientSerializer(patient_profile)
                    user_data['patient_profile'] = patient_serializer.data
                except Patient.DoesNotExist:
                    user_data['patient_profile'] = None
            elif user.role == 'doctor':
                 try:
                    doctor_profile = user.doctor_profile
                    # Use the appropriate serializer for the profile
                    doctor_serializer = DoctorSerializer(doctor_profile) # Make sure DoctorSerializer is defined correctly
                    user_data['doctor_profile'] = doctor_serializer.data
                 except Doctor.DoesNotExist:
                    user_data['doctor_profile'] = None
            return Response(user_data) # No need for status=status.HTTP_200_OK explicitly

        elif request.method == 'PUT':
             # Use partial=True for PUT as well to allow partial updates easily
             user_serializer = self.get_serializer(user, data=request.data, partial=True)
             try:
                 user_serializer.is_valid(raise_exception=True)
             except serializers.ValidationError as e:
                  # Return specific validation errors
                  return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

             profile_serializer = None
             profile_data_key = None
             profile_errors = None
             profile_updated = False

             # Logic to handle nested patient_profile update
             if user.role == 'patient':
                  profile_data_key = 'patient_profile'
                  if profile_data_key in request.data:
                     patient_data = request.data.get(profile_data_key)
                     if isinstance(patient_data, dict):
                         try:
                             patient_profile = user.patient_profile
                             # Ensure PatientSerializer allows partial updates
                             profile_serializer = PatientSerializer(patient_profile, data=patient_data, partial=True)
                         except Patient.DoesNotExist:
                              profile_errors = {"detail": "Patient profile not found for this user."}
                     else:
                         profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}

             # Logic to handle nested doctor_profile update
             elif user.role == 'doctor':
                  profile_data_key = 'doctor_profile'
                  if profile_data_key in request.data:
                      doctor_data = request.data.get(profile_data_key)
                      if isinstance(doctor_data, dict):
                           try:
                               doctor_profile = user.doctor_profile
                               # Ensure DoctorSerializer allows partial updates (it might be read-only now)
                               # You might need a different serializer for updating the doctor profile via 'me'
                               # Or adjust DoctorSerializer to handle updates if needed elsewhere
                               profile_serializer = DoctorSerializer(doctor_profile, data=doctor_data, partial=True) # Adjust if DoctorSerializer is read-only
                           except Doctor.DoesNotExist:
                                profile_errors = {"detail": "Doctor profile not found for this user."}
                      else:
                           profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}


             if profile_serializer:
                 try:
                     profile_serializer.is_valid(raise_exception=True)
                     profile_updated = True
                 except serializers.ValidationError as e:
                     profile_errors = e.detail # Collect profile validation errors

             # Check for errors before saving
             if profile_errors:
                  # Combine errors if necessary or return profile errors separately
                  return Response({f"{profile_data_key}_errors": profile_errors}, status=status.HTTP_400_BAD_REQUEST)
             else:
                  # Save user data first
                  user_instance = user_serializer.save()

                  # Save profile data if updated
                  if profile_updated and profile_serializer:
                      profile_serializer.save()

                  # Return updated data (re-serialize the instance after save)
                  final_serializer = self.get_serializer(user_instance) # Re-serialize the user
                  final_response_data = final_serializer.data
                   # Add updated profile data back
                  if user.role == 'patient':
                     try: final_response_data['patient_profile'] = PatientSerializer(user_instance.patient_profile).data
                     except Patient.DoesNotExist: final_response_data['patient_profile'] = None
                  elif user.role == 'doctor':
                      try: final_response_data['doctor_profile'] = DoctorSerializer(user_instance.doctor_profile).data
                      except Doctor.DoesNotExist: final_response_data['doctor_profile'] = None

                  return Response(final_response_data)

#


class DoctorViewSet(viewsets.ReadOnlyModelViewSet): # <--- To this (Safer for public access)
    """
    API endpoint that allows PUBLIC viewing of doctors list and details.
    Uses prefetching for optimization.
    """
    # --- استخدم السيريالايزر المعدل ---
    serializer_class = DoctorSerializer

    # --- اسمح لأي شخص بالوصول (للقراءة فقط بسبب ReadOnlyModelViewSet) ---
    permission_classes = [AllowAny]

    # --- Queryset محسن باستخدام select_related ---
    queryset = Doctor.objects.select_related(
        'user',         # Fetch related CustomUser
        'user__city',   # Fetch related City through CustomUser
        'user__area'  # Fetch related Area through CustomUser
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
    """Handles listing all available times and creating new ones."""
    
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        doctor_id = request.query_params.get("doctor_id")
        if not doctor_id or doctor_id == 'null':
            return Response({'error': 'doctor_id is required'}, status=400)
        try:
            doctor_id = int(doctor_id)
        except ValueError:
            return Response({'error': 'doctor_id must be an integer'}, status=400)
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
    """Handles retrieving, updating, and deleting specific available times."""
    
    # permission_classes = [permissions.IsAuthenticated]

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







#=======appointments================

class AppointmentListCreateView(APIView):
    def get(self, request):
        doctor_id = request.GET.get("doctor_id")
        patient_id = request.GET.get("patient_id")
        
        # Start with all appointments
        appointments = Appointment.objects.all()
        
        # Apply filters conditionally
        if patient_id:
            appointments = appointments.filter(patient_id=patient_id)
        if doctor_id:
            appointments = appointments.filter(doctor_id=doctor_id)
        
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        data = request.data.copy()

        # لو المستخدم مسجل ومفيش patient جاي من الفورم، نستخدم الحالي
        if not data.get("patient"):
            try:
                patient = Patient.objects.get(user=request.user)
                data["patient"] = patient.id
            except Patient.DoesNotExist:
                return Response(
                    {"detail": "Patient profile not found for this user."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = AppointmentSerializer(data=data)

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



#  feedback
class FeedbackListCreateView(APIView):
    def get(self, request):
     
        doctor_id = request.GET.get("doctor_id")
        ordering = request.GET.get("ordering", "-created_at")

        allowed_ordering_fields = ["created_at", "-created_at", "rate", "-rate"]

        if ordering not in allowed_ordering_fields:
            ordering = "-created_at"  

        if doctor_id:
            feedbacks = Feedback.objects.filter(doctor_id=doctor_id)
        else:
            feedbacks = Feedback.obj
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
    """
    Login endpoint specifically for admin users.
    Returns JWT tokens only if the user has role='admin'.
    """
    serializer_class = AdminTokenObtainPairSerializer
    permission_classes = [AllowAny] # 


class AdminFeedbackListView(generics.ListAPIView):
    """
    Admin view to list all feedbacks.
    Allows filtering by is_active status.
    """
    serializer_class = FeedbackSerializer
    permission_classes = [IsAdminRole] # فقط الأدمن يمكنه الوصول

    def get_queryset(self):
        queryset = Feedback.objects.select_related('patient__user', 'doctor__user').all().order_by('-created_at')
        is_active_filter = self.request.query_params.get('is_active')
        if is_active_filter is not None:
             if is_active_filter.lower() == 'true':
                 queryset = queryset.filter(is_active=True)
             elif is_active_filter.lower() == 'false':
                 queryset = queryset.filter(is_active=False)
        return queryset

# In clinic/views.py

# --- 👇 تغيير هنا ---
class AdminFeedbackDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin view to retrieve, update, and delete a specific feedback entry.
    Allows admin to change 'is_active', 'feedback', 'rate', and 'admin_notes'.
    """
    # --- 👇 تأكد أن السيريالايزر يسمح بالكتابة لهذه الحقول ---
    serializer_class = FeedbackSerializer
    permission_classes = [IsAdminRole] # فقط الأدمن يمكنه الوصول
    queryset = Feedback.objects.all()

    # --- 👇 override perform_update و perform_destroy لتحديث تقييم الطبيب ---
    def perform_update(self, serializer):
        # استدعاء الحفظ العادي أولاً
        instance = serializer.save()
        # تحديث تقييم الطبيب بعد التعديل (خاصة إذا تم تعديل الـ rate)
        if instance.doctor:
             instance.doctor.update_rating() # افترض وجود هذه الدالة في موديل Doctor

    def perform_destroy(self, instance):
        doctor = instance.doctor # احصل على الطبيب قبل الحذف
        instance.delete()
        # تحديث تقييم الطبيب بعد الحذف
        if doctor:
             doctor.update_rating()
