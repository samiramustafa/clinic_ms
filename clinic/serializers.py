
from rest_framework import serializers
from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import Appointment, AvailableTime


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    doctor_profile = serializers.SerializerMethodField()
    # image = serializers.ImageField(required=False, allow_null=True)  
    # date_of_birth = serializers.DateField(required=False, allow_null=True)  

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'phone_number', 'role', 'city', 'area', 'national_id', 'password', 'doctor_profile' ]

    def get_doctor_profile(self, obj):
        """ ✅ استرجاع بيانات الطبيب إذا كان المستخدم طبيبًا """
        if hasattr(obj, 'doctor_profile'):
            return {
                "speciality": obj.doctor_profile.speciality,
                "image": obj.doctor_profile.image.url if obj.doctor_profile.image else None,
                "fees": obj.doctor_profile.fees,
                "description": obj.doctor_profile.description,
               
            }
        return None

    def validate_date_of_birth(self, value):
        """ ✅ التأكد من أن عمر المريض لا يقل عن 18 سنة """
        if value:
            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            if age < 18:
                raise serializers.ValidationError("Patient must be at least 18 years old.")
        return value

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        image = validated_data.pop("image", None)
        birth_date = validated_data.pop("date_of_birth", None)  # ✅ تغيير الاسم ليتوافق مع `models.py`

        user = CustomUser.objects.create(**validated_data)

        if user.role == "doctor":
            speciality = self.initial_data.get("speciality", "General")
            doctor = Doctor.objects.create(user=user, speciality=speciality)
            if image:
                doctor.image = image
                doctor.save()

        elif user.role == "patient":
            gender = self.initial_data.get("gender", "male")
            if not birth_date:
                raise serializers.ValidationError({"birth_date": "Patient must provide a valid birth date."})
            Patient.objects.create(user=user, gender=gender, birth_date=birth_date)  # ✅ استخدام `birth_date` الصحيح

        return user
# Serializer for Doctor
class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    class Meta:
        model = Doctor
        fields = '__all__'

# Serializer for Patient
class PatientSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
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
    doctor_name = serializers.SerializerMethodField(read_only=True)
    patient_name = serializers.CharField(
        max_length=255, 
         
        allow_blank=True,
         # تعيين القيمة الافتراضية لتكون فارغة في البداية
    )

    class Meta:
        model = Appointment
        fields = (
            "id", "patient", "doctor", "available_time", "date", "time_range",
            "patient_name", "doctor_name", "status", "phone_number"
        )
        read_only_fields = (
            "id", "date", "time_range", "doctor_name", "status"
        )

    def get_time_range(self, obj):
        if obj.available_time:
            return f"{obj.available_time.start_time} - {obj.available_time.end_time}"
        return None

    def get_doctor_name(self, obj):
        return obj.doctor.user.username if obj.doctor and obj.doctor.user else None

    def validate(self, data):
        available_time = data.get("available_time")
        doctor = data.get("doctor")
        patient = data.get("patient")
        phone_number = data.get("phone_number")

        # التحقق من أن available_time ينتمي للطبيب
        if available_time and doctor and available_time.doctor != doctor:
            raise serializers.ValidationError({
                "available_time": "The selected available time does not belong to the chosen doctor."
            })

        # التأكد من وجود مريض
        if not patient:
            raise serializers.ValidationError({
                "patient": "Patient is required."
            })

        # التحقق من رقم الهاتف
        if phone_number and (not phone_number.isdigit() or len(phone_number) > 11):
            raise serializers.ValidationError({
                "phone_number": "Enter a valid phone number with a maximum of 11 digits."
            })

        # تعيين الاسم الافتراضي للمريض بناءً على بيانات الـ User المرتبط
        if not data.get("patient_name") and patient:
            # جلب اسم المريض من الـ User المرتبط
            data["patient_name"] = patient.user.username if patient.user else ""

        return data






# ===feedbacks================

class FeedbackSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.user.username", read_only=True)

    class Meta:
        model = Feedback
        fields = ["id", "patient","patient_name", "doctor", "feedback", "rate", "created_at"]




