
from datetime import datetime
from rest_framework import serializers
from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import Appointment, AvailableTime

class UserSerializer(serializers.ModelSerializer):

    gender = serializers.ChoiceField(choices=Patient.gender.field.choices, required=False, write_only=True, allow_blank=True)
    birth_date = serializers.DateField(required=False, write_only=True, allow_null=True)
    speciality = serializers.CharField(max_length=100, required=False, write_only=True, allow_blank=True)
    description = serializers.CharField(required=False, write_only=True, allow_blank=True, allow_null=True)
    fees = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, write_only=True, allow_null=True)
    image = serializers.ImageField(required=False, write_only=True, allow_null=True)
    # city=serializers.CharField(source='city.name', read_only=True)
    # area=serializers.CharField(source='area.name', read_only=True)
    card=serializers.CharField(required=False, write_only=True, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'full_name', 'phone_number', 'role', 'city', 'area','email',
            'national_id', 'password','card',
            'gender', 'birth_date', 'speciality', 'description', 'fees', 'image'
        ]

    def validate(self, data):
        role = data.get('role')
        if role == 'patient':
            birth_date = data.get('birth_date')
            if birth_date:
                today = date.today()
                try:
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    if age < 18:
                        raise serializers.ValidationError({"birth_date": "Patients must be at least 18 years old."})
                except AttributeError:
                     raise serializers.ValidationError({"birth_date": "Invalid date format provided."})
        return data


    def create(self, validated_data):
        # --- 👇 عدّل الـ create عشان تستخدم الحقول دي وتنشئ البروفايل صح ---
        gender = validated_data.pop('gender', None)
        birth_date = validated_data.pop('birth_date', None)
        speciality = validated_data.pop('speciality', "General") # قيمة افتراضية
        description = validated_data.pop('description', None)
        fees = validated_data.pop('fees', None)
        image = validated_data.pop('image', None)

        validated_data["password"] = make_password(validated_data["password"])
        user = CustomUser.objects.create(**validated_data)

        if user.role == "doctor":
            Doctor.objects.create(user=user, speciality=speciality, description=description, fees=fees, image=image)
        elif user.role == "patient":
            Patient.objects.create(user=user, gender=gender or 'male', birth_date=birth_date)

        return user

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    birth_date = serializers.DateField(required=False, allow_null=True)  

    class Meta:
        model = Patient
        fields = '__all__'
class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name']
        
class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'name', 'city']

class AvailableTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableTime
        fields = "__all__"


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




