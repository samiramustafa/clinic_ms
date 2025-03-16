from django.utils import timezone
from django.db import models
import re
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
from datetime import date, timedelta


from django.utils.translation import gettext_lazy as _  



class GenderChoices(models.TextChoices):
    MALE = "M", _("Male")
    FEMALE = "F", _("Female")

class RoleChoices(models.TextChoices):
    ADMIN = "admin", _("Admin")
    DOCTOR = "doctor", _("Doctor")
    PATIENT = "patient", _("Patient")

class StatusChoices(models.TextChoices):
    PENDING = "pending", _("Pending")
    ACCEPTED = "accepted", _("Accepted")
    REJECTED = "rejected", _("Rejected")

class DaysChoices(models.TextChoices):
    MONDAY = "Monday", _("Monday")
    TUESDAY = "Tuesday", _("Tuesday")
    WEDNESDAY = "Wednesday", _("Wednesday")
    THURSDAY = "Thursday", _("Thursday")
    FRIDAY = "Friday", _("Friday")
    SATURDAY = "Saturday", _("Saturday")
    SUNDAY = "Sunday", _("Sunday")


validate_phone_number = RegexValidator(
    regex=r"^(010|011|012|015)\d{8}$",
    message="Phone number must be 11 digits and start with 010, 011, 012, or 015."
)

validate_national_id = RegexValidator(
    regex=r"^\d{14}$",
    message="National ID must be exactly 14 digits."
)

validate_name = RegexValidator(
    regex=r"^[a-zA-Z\s]+$",
    message="Name must contain only letters and spaces."
)

def validate_time_order(start_time, end_time):
    if start_time is None or end_time is None:
        return
    if start_time >= end_time:
        raise ValidationError("Start time must be before end time.")

#  main user  ##

class User(AbstractUser):
    national_id = models.CharField(
        max_length=14, unique=True, null=True, blank=True, validators=[validate_national_id]
    )
    name = models.CharField(max_length=50, validators=[validate_name])
    email = models.EmailField(unique=True)
    mobile_phone = models.CharField(
        max_length=11, unique=True, null=True, blank=True, validators=[validate_phone_number]
    ) 
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    gender = models.CharField(
        max_length=1, choices=GenderChoices.choices, null=True, blank=True
    )
    birth_date = models.DateField(null=True, blank=True)
    role = models.CharField(
        max_length=10, choices=RoleChoices.choices, default=RoleChoices.PATIENT, blank=True
    )

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_groups",
        blank=True,
        help_text="The groups this user belongs to.",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
    )

    def clean(self):
        super().clean()
        if self.birth_date and self.birth_date > timezone.now().date():
            raise ValidationError("Birth date cannot be in the future.")

    def __str__(self):
        return self.name

# ======patient model ========

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    address = models.TextField(null=True, blank=True)
    medical_history = models.TextField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.user.role != RoleChoices.PATIENT:
            raise ValidationError("This profile can only be a user with role 'patient'.")
        if self.medical_history and len(self.medical_history.strip()) < 10:
            raise ValidationError("Medical history must be at least 10 characters ")

    def __str__(self):
        return self.user.name

# ======doctor model ========

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    specialization = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])

    def clean(self):
        super().clean()
        if self.user.role != RoleChoices.DOCTOR:
            raise ValidationError("This profile can only be a user with role 'doctor'.")
        if len(self.specialization.strip()) < 3:
            raise ValidationError("Specialization must be at least 3 characters long.")
        if self.description and len(self.description.strip()) < 10:
            raise ValidationError("Description must be at least 10 characters ")

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
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default="pending")


    def clean(self):
        validate_time_order(self.start_time, self.end_time)

    def __str__(self):
        return f"{self.patient.user.name} - {self.doctor.user.name} ({self.date})"

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

class AvailableTime(models.Model):
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="available_times"
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    day = models.CharField(max_length=20, choices=DaysChoices.choices, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    def clean(self):
        validate_time_order(self.start_time, self.end_time)

        if not self.doctor:
            raise ValidationError(_("Doctor field is required."))

        days_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }

        if self.day and self.date:
     
            selected_weekday = days_map.get(self.day)
            if selected_weekday is not None and self.date.weekday() != selected_weekday:
                raise ValidationError(_("The selected date does not match the chosen day."))

        elif self.day and not self.date:
    
            today = date.today()
            today_weekday = today.weekday()
            selected_weekday = days_map[self.day]

            days_difference = (selected_weekday - today_weekday) % 7
            if days_difference == 0:
                days_difference = 7 

            self.date = today + timedelta(days=days_difference)

        elif not self.day and not self.date:
            raise ValidationError(_("You must specify either a day or a specific date."))

    def __str__(self):
        return f"{self.doctor.user.name} - {self.day or self.date} ({self.start_time} - {self.end_time})"

