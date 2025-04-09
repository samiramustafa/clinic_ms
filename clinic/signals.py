# clinic/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Appointment

@receiver(post_save, sender=Appointment)
def send_appointment_confirmation_email(sender, instance, created, update_fields, **kwargs):
    """
    Sends an email when an appointment status is updated to 'accepted'.
    """
    # طريقة أبسط: أرسل فقط إذا الحالة الحالية 'accepted'
    # (قد تحتاج لتحسين لمنع الإرسال المتكرر إذا تم الحفظ مرة أخرى بنفس الحالة)
    if not created and instance.status == 'accepted':
        # --- نضيف تحقق إضافي لمعرفة هل الحالة كانت مختلفة قبل الحفظ؟ ---
        # كحل مؤقت، سنرسل الإيميل كل مرة يتم الحفظ والحالة accepted.

        patient_user = instance.patient.user
        if patient_user.email:
            try:
                subject = f"Appointment Confirmed with Dr. {instance.doctor.user.full_name}"
                message = f"""Dear {patient_user.full_name},

Your appointment has been confirmed:

Doctor: Dr. {instance.doctor.user.full_name} ({instance.doctor.speciality})
Date: {instance.available_time.date.strftime('%Y-%m-%d')}
Time: {instance.available_time.start_time.strftime('%I:%M %p')} - {instance.available_time.end_time.strftime('%I:%M %p')}
Location: [Add Clinic Address Here if available]

Instructions:
- Payment is Cash only at the clinic.
- Please arrive on time. If you are late, your appointment may be cancelled.

Thank you,
Clinic Tech Team
"""
                # --- 👇 تم تعديل المسافة البادئة هنا ---
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [patient_user.email],
                    fail_silently=False, # اجعله True في الإنتاج لرؤية الأخطاء في اللوج فقط
                )
                # --- 👇 وتم تعديل المسافة البادئة هنا أيضًا ---
                print(f"Confirmation email sent successfully via signal to {patient_user.email}")

            except Exception as e:
                # هذه المسافة صحيحة (تحت except)
                print(f"ERROR sending confirmation email via signal to {patient_user.email}: {e}")
        else:
             # هذه المسافة صحيحة (تحت else)
            print(f"Patient {patient_user.username} does not have an email address (Signal).")