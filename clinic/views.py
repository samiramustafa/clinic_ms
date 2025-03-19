from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import viewsets
from .models import Appointment, AvailableTime, Feedback, User, Patient, Doctor
from .serializers import AppointmentSerializer, AvailableTimeSerializer, FeedbackSerializer, UserSerializer, PatientSerializer, DoctorSerializer
from rest_framework.response import Response
from rest_framework import status, permissions


# class UserListCreateView(generics.ListCreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

# class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer



class RegisterView(APIView):
    def post(self, request):
        user_data = {
            "username": request.data.get("username"),
            "email": request.data.get("email"),
            "password": request.data.get("password"),
            "role": request.data.get("role")
        }

        user_serializer = UserSerializer(data=user_data)
        if not user_serializer.is_valid():
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        user = user_serializer.save()
        user.set_password(request.data["password"])  # تأكد من تشفير كلمة المرور
        user.save()

        if user.role == "patient":
            patient_data = {
                "user": user.id,  # استخدم `id` بدلًا من `user` نفسه
                "address": request.data.get("address"),
                "medical_history": request.data.get("medical_history", ""),
            }
            serializer = PatientSerializer(data=patient_data)
        elif user.role == "doctor":
            doctor_data = {
                "user": user.id,
                "specialization": request.data.get("specialization"),
                "description": request.data.get("description", ""),
                "fees": request.data.get("fees", "0.00"),
            }
            serializer = DoctorSerializer(data=doctor_data)
        else:
            return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

#         serializer = UserSerializer(user, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk):
#         user = get_object_or_404(User, pk=pk)
#         user.delete()
#         return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)




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


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

