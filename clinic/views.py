from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import viewsets
from .models import Appointment, AvailableTime, Feedback, User, Patient, Doctor
from .serializers import AppointmentSerializer, AvailableTimeSerializer, FeedbackSerializer, UserSerializer, PatientSerializer, DoctorSerializer
from rest_framework.response import Response
from rest_framework import status, permissions

from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework import status



from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView




class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
   
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         user = self.user

#         if not user.is_active:
#             raise serializers.ValidationError("🚫 هذا الحساب غير مفعل.")

#         # ✅ أضف بيانات المستخدم إلى التوكن
#         data['username'] = user.username
#         # data['role'] = "doctor" if user.is_staff else "patient"
#         # data['role'] = user.role
#         if user.groups.filter(name="Doctor").exists():
#             data['role'] = "doctor"
#         elif user.groups.filter(name="Patient").exists():
#             data['role'] = "patient"
#         else:
#             data['role'] = "admin"

#         return data






# class CustomTokenObtainPairView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer




class AvailableTimeListCreateView(APIView):
    """Handles listing all available times and creating new ones."""
    
    # permission_classes = [permissions.IsAuthenticated]

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

        if doctor_id:
            appointments = Appointment.objects.filter(doctor_id=doctor_id)
        else:
            appointments = Appointment.objects.all()

        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        doctor_id = request.data.get("doctor")
        available_time_id = request.data.get("available_time")

        # التحقق من أن available_time يخص الطبيب المحدد
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



#  feedback
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


