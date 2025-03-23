from rest_framework import serializers
from .models import Appointment, Feedback, User, AvailableTime, Patient, Doctor
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "national_id",
            "name",
            "email",
            "username",
            "mobile_phone",
            "gender",
            "birth_date",
            "role",
            "password",
            "profile_picture",
        ] 


class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Doctor
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Patient
        fields = '__all__'



class AvailableTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableTime
        fields = "__all__"



# class AppointmentSerializer(serializers.ModelSerializer):
#     date = serializers.DateField(source="available_time.date", read_only=True)
#     time_range = serializers.SerializerMethodField()

#     class Meta:
#         model = Appointment
#         fields = ("id", "patient", "doctor", "available_time", "date", "time_range", "status")

#     def get_time_range(self, obj):
#         return f"{obj.available_time.start_time} - {obj.available_time.end_time}" if obj.available_time else None

#     def validate(self, data):
 
#         available_time = data.get("available_time")
#         doctor = data.get("doctor")

#         if available_time and doctor and available_time.doctor != doctor:
#             raise serializers.ValidationError(
#                 {"available_time": "The selected available time does not belong to the chosen doctor."}
#             )

#         return data

from rest_framework import serializers
from .models import Appointment, AvailableTime

class AppointmentSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source="available_time.date", read_only=True)
    time_range = serializers.SerializerMethodField(read_only=True)
    patient_name = serializers.SerializerMethodField(read_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = (
            "id", "patient", "doctor", "available_time", "date", "time_range",
            "patient_name", "doctor_name", "status","phone_number"
        )
        read_only_fields = ("id", "date", "time_range", "patient_name", "doctor_name")

    def get_time_range(self, obj):
       
        if obj.available_time:
            return f"{obj.available_time.start_time} - {obj.available_time.end_time}"
        return None

    def get_patient_name(self, obj):

        return obj.patient.user.name if obj.patient and obj.patient.user else None

    def get_doctor_name(self, obj):
      
        return obj.doctor.user.name if obj.doctor and obj.doctor.user else None
    def get_phone_number(self, obj):
   
        if obj.patient and obj.patient.user and hasattr(obj.patient.user, "mobile_phone"):
            return obj.patient.user.mobile_phone

    def validate(self, data):
       
        available_time = data.get("available_time")
        doctor = data.get("doctor")
        patient = data.get("patient")
        patient_phone = data.get("patient_phone")

        # التحقق من أن available_time ينتمي إلى الطبيب
        if available_time and doctor and available_time.doctor != doctor:
            raise serializers.ValidationError(
                {"available_time": "The selected available time does not belong to the chosen doctor."}
            )

        # التحقق من أن patient موجود
        if not patient:
            raise serializers.ValidationError(
                {"patient": "Patient is required."}
            )

        # التحقق من patient_phone إذا تم إرساله (اختياري لأنه blank=True)
        if patient_phone and len(patient_phone) > 11:
            raise serializers.ValidationError(
                {"patient_phone": "Phone number must not exceed 11 characters."}
            )

        return data




# ===feedbacks================

class FeedbackSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.user.name", read_only=True)

    class Meta:
        model = Feedback
        fields = ["id", "patient","patient_name", "doctor", "feedback", "rate", "created_at"]




