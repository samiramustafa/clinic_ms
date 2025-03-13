from django.db import models
import re
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


# Create your models here.
GENDER_CHOICES = [
     ("M", "Male"), 
     ("F", "Female")
     ]
ROLE_CHOICES = [(
      "admin", "Admin"), ("doctor", "Doctor"), ("patient", "Patient")
      ]
STATUS_CHOICES=[
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

DAYS=[
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
]
def validate_phone_number(value):
    if not re.match(r"^(010|011|012|015)\d{8}$", value):
        raise ValidationError("Phone number must be 11 digits and start with 010, 011, 012, or 015.")
    
def validate_national_id(value):
    if not re.match(r"^\d{14}$", value):
        raise ValidationError("National ID must be exactly 14 digits.")

def validate_time_order(start_time, end_time):
    if start_time is None or end_time is None:
        return
    if start_time >= end_time:
        raise ValidationError("Start time must be before end time.")

class User(AbstractUser):
    national_id = models.CharField(max_length=14, unique=True, null=True, blank=True, validators=[validate_national_id])
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    mobile_phone = models.CharField(
        max_length=11, unique=True, null=True, blank=True, validators=[validate_phone_number]
    ) 
    profile_picture = models.FileField(upload_to='profile_pics/', blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="patient")

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_groups",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def __str__(self):
        return f"{self.name}"

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    address = models.TextField(null=True, blank=True)
    medical_history = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.user.name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    specialization = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True) 
    fees = models.DecimalField(max_digits=10, decimal_places=2)    
    def __str__(self):
        return f"Dr. {self.user.name} - {self.specialization}"

class Feedback(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="feedbacks")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="feedbacks")
    feedback = models.TextField()
    rate = models.PositiveSmallIntegerField( validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.patient.user.name} to {self.doctor.user.name}"

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.patient.user.name} - {self.doctor.user.name} ({self.date})"

class AvailableTime(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="available_times")
    start_time = models.TimeField()
    end_time = models.TimeField()
    day = models.CharField(max_length=20, choices=DAYS)
    date = models.DateField(null=True, blank=True)

    def clean(self):
        validate_time_order(self.start_time, self.end_time)

    def __str__(self):
        return f"{self.doctor.user.name} - {self.day} ({self.start_time} - {self.end_time})"
