
from datetime import datetime
from rest_framework import serializers
from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import Appointment, AvailableTime
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer

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
    # --- الحقول الجديدة اللي هتجيب بيانات من CustomUser المرتبط ---
    name = serializers.CharField(source='user.full_name', read_only=True)
    # لاحظ: City و Area هما ForeignKeys في CustomUser، عشان نجيب الاسم محتاجين .name
    city = serializers.CharField(source='user.city.name', read_only=True, allow_null=True) # Handle cases where city might be null
    area = serializers.CharField(source='user.area.name', read_only=True, allow_null=True) # Handle cases where area might be null
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    class Meta:
        model = Doctor
        # --- حدد الحقول اللي عايزها تظهر في الـ API response ---
        fields = [
            'id',           # Doctor ID
            'user',       # شيل ده لو مش عايز الـ ID يظهر باسم 'user'
            # 'user_id',    # أو استخدم ده لو عايز الـ ID
            'name',         # اسم الطبيب (من CustomUser)
            'city',         # اسم المدينة (من CustomUser -> City)
            'area',         # اسم المنطقة (من CustomUser -> Area)
            'speciality',   # تخصص الطبيب (من Doctor)
            'description',  # وصف الطبيب (من Doctor)
            'fees',         # رسوم الكشف (من Doctor)
            'image',        # صورة الطبيب (من Doctor)
            'average_rating'# متوسط التقييم (من Doctor)
            # ضيف أي حقول تانية محتاجها من موديل Doctor
        ]
        read_only_fields = ['name', 'city', 'area', 'average_rating'] # الحقول دي للقراءة فقط هنا

class AdminUserSerializer(serializers.ModelSerializer):
    # يمكن إضافة حقول من بروفايل المريض/الطبيب إذا لزم الأمر
    patient_profile_exists = serializers.SerializerMethodField()
    doctor_profile_exists = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'full_name', 'email', 'phone_number', 'role',
            'city', 'area', 'national_id', # قد لا تحتاج لكل هذا، اختر ما يهم الأدمن
            'is_active', # حقل is_active الخاص بـ Django User مفيد
            'date_joined',
            'patient_profile_exists',
            'doctor_profile_exists',
        ]
        read_only_fields = fields # هذا السيريالايزر للعرض فقط من قبل الأدمن

    def get_patient_profile_exists(self, obj):
        return hasattr(obj, 'patient_profile')

    def get_doctor_profile_exists(self, obj):
        return hasattr(obj, 'doctor_profile')
class PatientSerializer(serializers.ModelSerializer):
    birth_date = serializers.DateField(required=False, allow_null=True)  

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

# class FeedbackSerializer(serializers.ModelSerializer):
#     patient_name = serializers.CharField(source="patient.user.username", read_only=True)

#     class Meta:
#         model = Feedback
#         fields = ["id", "patient","patient_name", "doctor", "feedback", "rate", "created_at"]

# In clinic/serializers.py

class FeedbackSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.user.username", read_only=True)
    doctor_name = serializers.CharField(source="doctor.user.full_name", read_only=True)

    class Meta:
        model = Feedback
        fields = [
            "id", "patient", "patient_name", "doctor", "doctor_name",
            "feedback", # <-- قابل للتعديل
            "rate",     # <-- قابل للتعديل
            "created_at",
            "is_active", # <-- قابل للتعديل
            "admin_notes" # <-- قابل للتعديل
        ]
        # --- 👇 أزل أي حقول تريد تعديلها من هنا ---
        # read_only_fields = ['patient_name', 'doctor_name', 'created_at', 'patient', 'doctor']
        # أو يمكنك تحديد الحقول القابلة للقراءة فقط بوضوح:
        read_only_fields = ['patient_name', 'doctor_name', 'created_at']
        # لاحظ: patient و doctor يجب أن يكونا للقراءة فقط عادةً لتجنب تغيير لمن يخص التقييم

    # --- 👇 (اختياري ولكن مهم) إضافة تحقق للتأكد أن الـ rate ضمن الحدود عند التعديل ---
    def validate_rate(self, value):
         if not (1 <= value <= 5):
             raise serializers.ValidationError("Rate must be between 1 and 5.")
         return value


class AdminTokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # التحقق من دور المستخدم بعد المصادقة الناجحة
        if not self.user.role == 'admin':
            # يمكنك استخدام is_staff بدلاً من role إذا كان هو المحدد للأدمن
            # if not self.user.is_staff:
            raise serializers.ValidationError("Access denied. User is not an admin.")
        # يمكنك إضافة بيانات المستخدم هنا إذا أردت إرجاعها مع التوكن
        # data['user_role'] = self.user.role
        return data
