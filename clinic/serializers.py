from rest_framework import serializers
from .models import User, AvailableTime
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "national_id", "name", "email", "mobile_phone",
            "profile_picture", "gender", "birth_date", "role", "password","date_joined", "last_login"
        ]  

        extra_kwargs = {
            "password": {"write_only": True}  
        }

    def create(self, validated_data):
    
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.password = make_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
       
        password = validated_data.pop('password', None)
        
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
      
        if password is not None:
            instance.password = make_password(password)
            
        instance.save()
        return instance





# avaliable in the clinic_ms/clinic/serializers.py file


class AvailableTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableTime
        fields = "__all__"




