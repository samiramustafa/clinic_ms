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




