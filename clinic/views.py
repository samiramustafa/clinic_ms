<<<<<<< HEAD
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import viewsets
from .models import Appointment, AvailableTime, Feedback, User
from .serializers import AppointmentSerializer, AvailableTimeSerializer, FeedbackSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework import status, permissions


# class UserListCreateView(generics.ListCreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

# class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer




class UserListCreateAPIView(APIView):
    def get(self, request):
        all_users = User.objects.all()
        serializer = UserSerializer(all_users, many=True)  
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailAPIView(APIView):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)




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
=======
from rest_framework import viewsets
from .models import User, Patient, Doctor
from .serializers import UserSerializer, PatientSerializer, DoctorSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
>>>>>>> main
