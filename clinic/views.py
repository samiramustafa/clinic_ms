# from rest_framework import viewsets
# from .models import User, Patient, Doctor
# from .serializers import UserSerializer, PatientSerializer, DoctorSerializer

# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

# class PatientViewSet(viewsets.ModelViewSet):
#     queryset = Patient.objects.all()
#     serializer_class = PatientSerializer

# class DoctorViewSet(viewsets.ModelViewSet):
#     queryset = Doctor.objects.all()
#     serializer_class = DoctorSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, Patient, Doctor
from .serializers import UserSerializer, PatientSerializer, DoctorSerializer

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

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            user.delete()  # حذف المستخدم إذا فشل التسجيل
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
