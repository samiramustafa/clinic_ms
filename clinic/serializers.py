# from rest_framework import serializers
# from .models import User, Patient, Doctor

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = '__all__'

# class PatientSerializer(serializers.ModelSerializer):
#     user = UserSerializer()

#     class Meta:
#         model = Patient
#         fields = '__all__'

# class DoctorSerializer(serializers.ModelSerializer):
#     user = UserSerializer()

#     class Meta:
#         model = Doctor
#         fields = '__all__'
from rest_framework import serializers
from .models import User, Patient, Doctor

from rest_framework import serializers
from .models import User, Patient, Doctor

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'name': {'required': False},  # ✅ اجعل `name` اختياريًا
        }

    def create(self, validated_data):
        name = validated_data.get('name', '')  # ✅ اجعل `name` اختياريًا حتى لو لم يتم إرساله
        user = User(
            email=validated_data['email'],
            username=validated_data.get('username', validated_data['email']),
            name=name,
            role=validated_data.get('role', 'patient'),
        )
        user.set_password(validated_data['password'])  # ✅ تشفير كلمة المرور
        user.save()
        return user

class PatientSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # ✅ الآن `user` يقبل ID بدلاً من Object

    class Meta:
        model = Patient
        fields = '__all__'

class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # ✅ نفس التعديل هنا

    class Meta:
        model = Doctor
        fields = '__all__'
