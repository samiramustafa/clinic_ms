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
        ] 

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Doctor
        fields = '__all__'
        read_only_fields = ['user']


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = [
#             "id", "national_id", "name", "email", "mobile_phone",
#             "profile_picture", "gender", "birth_date", "role", "password","date_joined", "last_login"
#         ]  

#         extra_kwargs = {
#             "password": {"write_only": True}  
#         }

#     def create(self, validated_data):
    
#         password = validated_data.pop('password', None)
#         user = super().create(validated_data)
#         if password:
#             user.password = make_password(password)
#             user.save()
#         return user

#     def update(self, instance, validated_data):
       
#         password = validated_data.pop('password', None)
        
        
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
            
      
#         if password is not None:
#             instance.password = make_password(password)
            
#         instance.save()
#         return instance








class AvailableTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableTime
        fields = "__all__"








class AppointmentSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source="available_time.date", read_only=True)
    time_range = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ("id", "patient", "doctor", "available_time", "date", "time_range", "status")

    def get_time_range(self, obj):
        return f"{obj.available_time.start_time} - {obj.available_time.end_time}" if obj.available_time else None

    def validate(self, data):
 
        available_time = data.get("available_time")
        doctor = data.get("doctor")

        if available_time and doctor and available_time.doctor != doctor:
            raise serializers.ValidationError(
                {"available_time": "The selected available time does not belong to the chosen doctor."}
            )

        return data
    


# ===feedbacks================

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta :
        model = Feedback
     
        fields = '__all__'



class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Patient
        fields = '__all__'

