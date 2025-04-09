from django.utils import timezone
from django.db import models
import re
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
from datetime import date, timedelta
from django.db.models import Avg
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


def validate_time_order(start_time, end_time):
    if start_time is None or end_time is None:
        return
    if start_time >= end_time:
        raise ValidationError("Start time must be before end time.")
    

# ======================  MODELS  ========================
# City Model
class City(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Area Model
class Area(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='areas')

    def __str__(self):
        return f"{self.name} - {self.city.name}"
# ======================  Custom User Model  ========================


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    ]

    # التحقق من رقم الهاتف
    validate_phone_number = RegexValidator(
        regex=r"^(010|011|012|015)\d{8}$",
        message="Phone number must be 11 digits and start with 010, 011, 012, or 015."
    )

    # التحقق من الرقم القومي
    validate_national_id = RegexValidator(
        regex=r"^\d{14}$",
        message="National ID must be exactly 14 digits."
    )

    # التحقق من الاسم
    validate_name = RegexValidator(
        regex=r"^[a-zA-Z\s]+$",
        message="Name must contain only letters and spaces."
    )

    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, blank=False, validators=[validate_name])
    phone_number = models.CharField(max_length=15, unique=True, validators=[validate_phone_number])
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, blank=False, null=False)
    city = models.ForeignKey("City", on_delete=models.SET_NULL, null=True, blank=True)
    area = models.ForeignKey("Area", on_delete=models.SET_NULL, null=True, blank=True)
    national_id = models.CharField(max_length=14, unique=True, blank=True, null=True, validators=[validate_national_id])

    first_name = models.CharField(max_length=150, blank=True, null=True, validators=[validate_name])
    last_name = models.CharField(max_length=150, blank=True, null=True, validators=[validate_name])
    email = models.EmailField(blank=True, null=True)
   

    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    def validate(self):
        """
        تأكد من صحة البيانات المدخلة.
        """
        # تحقق من أن الاسم الكامل يحتوي على أكثر من كلمتين
        if len(self.full_name.split()) < 2:
            raise ValidationError({"full_name": "Full name must contain at least two words."})

        # تحقق من أن الاسم الأول والأخير ليس فارغًا إذا تم إدخالهما
        if self.first_name and len(self.first_name.strip()) == 0:
            raise ValidationError({"first_name": "First name cannot be just spaces."})

        if self.last_name and len(self.last_name.strip()) == 0:
            raise ValidationError({"last_name": "Last name cannot be just spaces."})


  
    def __str__(self):
        return self.username



# ======patient model ========

class Patient(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile')
    birth_date = models.DateField(null=True, blank=True)
    medical_history = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], default='male')

    def clean(self):
        # 1️⃣ منع أن يكون المريض طبيبًا أيضًا
        if hasattr(self.user, 'doctor_profile'):
            raise ValidationError("This user is already registered as a Doctor.")

        # 2️⃣ التحقق من العمر (على الأقل 18 سنة)
        if self.birth_date:
            today = date.today()
            age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
            if age < 18:
                raise ValidationError("Patients must be at least 18 years old.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Patient: {self.user.full_name}"
# ======doctor model ========

class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='doctor_profile')
    speciality = models.CharField(max_length=100, default="General")
    description = models.TextField(null=True, blank=True)  # ✅ جعل الوصف اختيارياً    
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='doctor_images/', null=True, blank=True)
    average_rating = models.FloatField(default=0.0)

    def clean(self):
        if hasattr(self.user, 'patient_profile'):
            raise ValidationError("This user is already registered as a Patient.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def update_rating(self):
      
        feedbacks = self.feedbacks.all()
        new_average = round(sum(f.rate for f in feedbacks) / feedbacks.count(), 1) if feedbacks.exists() else 0.0

        if self.average_rating != new_average:  
            self.average_rating = new_average
            self.save()

    def __str__(self):
        return f"Dr. {self.user.full_name} - {self.speciality}"


    




class Feedback(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="feedbacks")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="feedbacks")
    feedback = models.TextField()
    rate = models.PositiveSmallIntegerField( validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True) # اجعل القيمة الافتراضية True (نشط)
    admin_notes = models.TextField(blank=True, null=True) # اختياري
   

    def save(self, *args, **kwargs):
        
        super().save(*args, **kwargs)
        self.doctor.update_rating()  

    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.doctor.update_rating() 
    
    # def __str__(self):
    #     return f"Feedback from {self.patient.user.username} to Dr. {self.doctor.user.username} - {self.rate} ⭐"
    def __str__(self):
         status = "Active" if self.is_active else "Inactive"
         return f"Feedback from {self.patient.user.username} to Dr. {self.doctor.user.username} ({self.rate} ⭐) - Status: {status}"


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
        return f"{self.doctor.user.username} - {self.day or self.date} ({self.start_time} - {self.end_time})"



class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    available_time = models.ForeignKey(AvailableTime, on_delete=models.CASCADE, related_name="appointments")
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default="pending")
   
    


    def __str__(self):
        return f"{self.patient.user.username} - {self.available_time.doctor.user.username} ({self.available_time.date} {self.available_time.start_time} - {self.available_time.end_time})"
from django.utils import timezone
from django.db import models
import re
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
from datetime import date, timedelta
from django.db.models import Avg
from django.utils.translation import gettext_lazy as _  

# ... (keep all your existing choices and validators) ...

class NewsletterSubscriber(models.Model):
    """
    Model for storing newsletter subscribers with fake email sending capability
    """
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_email_sent = models.DateTimeField(null=True, blank=True)
    email_count = models.PositiveIntegerField(default=0)

    def send_welcome_email(self):
        """
        Simulates sending a welcome email without actually sending it
        """
        # Print to console for development purposes
        print(f"\n=== Simulating welcome email to {self.email} ===\n")
        print(f"From: clinic@example.com")
        print(f"To: {self.email}")
        print(f"Subject: Welcome to Our Clinic Newsletter!")
        print(f"\nBody:")
        print(f"Dear Subscriber,")
        print(f"\nThank you for joining our clinic newsletter!")
        print(f"You'll receive updates on health tips, clinic news, and special offers.")
        print(f"\nWe're committed to your health and wellbeing.")
        print(f"\nBest regards,")
        print(f"The Clinic Team\n")
        print(f"=== End of simulated email ===\n")

        # Update tracking fields
        self.last_email_sent = timezone.now()
        self.email_count += 1
        self.save()

    def clean(self):
        """
        Basic email validation
        """
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            raise ValidationError("Please enter a valid email address.")

    def __str__(self):
        return f"{self.email} ({'Active' if self.is_active else 'Inactive'})"

# ... (keep all your existing models) ...

# Add this at the end of your models.py
class NewsletterLog(models.Model):
    """
    Optional model to track simulated email sends
    """
    subscriber = models.ForeignKey(NewsletterSubscriber, on_delete=models.CASCADE, related_name='logs')
    sent_at = models.DateTimeField(auto_now_add=True)
    email_type = models.CharField(max_length=50, default='welcome')
    simulated_content = models.TextField()

    def __str__(self):
        return f"Log for {self.subscriber.email} at {self.sent_at}"

    class Meta:
        ordering = ['-sent_at']