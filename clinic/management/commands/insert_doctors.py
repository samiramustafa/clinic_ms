from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
import os, random

from clinic.models import CustomUser, Doctor  # عدّل اسم التطبيق هنا

class Command(BaseCommand):
    help = 'Insert 30 random doctors and users'

    def handle(self, *args, **kwargs):
        first_names = ['Ahmed', 'Mohamed', 'Sara', 'Laila', 'Omar', 'Hana', 'Youssef', 'Nour', 'Khaled', 'Mona']
        last_names = ['Ali', 'Ibrahim', 'Hassan', 'Fahmy', 'Mostafa', 'Mahmoud', 'Tamer', 'Sayed', 'Kamel', 'Abdallah']
        specialities = ["Cardiologist", "Dermatologist", "Pediatrician", "Neurologist", "Psychiatrist", "Orthopedic", "Surgeon", "General"]
        descriptions = [
            "Experienced in patient care and diagnostics.",
            "Over 10 years in the medical field.",
            "Committed to providing quality healthcare.",
            "Passionate about helping people live healthier lives.",
            "Known for excellent communication with patients."
        ]

        def generate_phone():
            return random.choice(["010", "011", "012", "015"]) + ''.join([str(random.randint(0, 9)) for _ in range(8)])

        def generate_national_id():
            return ''.join([str(random.randint(0, 9)) for _ in range(14)])

        IMAGES_FOLDER = os.path.join(settings.MEDIA_ROOT, 'doctor_images')
        image_files = [f for f in os.listdir(IMAGES_FOLDER) if os.path.isfile(os.path.join(IMAGES_FOLDER, f))]

        for i in range(30):
            first = random.choice(first_names)
            last = random.choice(last_names)
            full = f"{first} {last}"
            username = f"dr_{first.lower()}{last.lower()}_{random.randint(100, 999)}"
            phone = generate_phone()
            nid = generate_national_id()

            user = CustomUser.objects.create(
                username=username,
                full_name=full,
                phone_number=phone,
                role='doctor',
                city_id=random.randint(1, 20),
                area_id=random.randint(1, 20),
                national_id=nid,
                first_name=first,
                last_name=last
            )

            image_filename = random.choice(image_files)
            image_path = os.path.join(IMAGES_FOLDER, image_filename)

            with open(image_path, 'rb') as img_file:
                Doctor.objects.create(
                    user=user,
                    speciality=random.choice(specialities),
                    description=random.choice(descriptions),
                    fees=round(random.uniform(100, 500), 2),
                    image=File(img_file, name=image_filename),
                )

        self.stdout.write(self.style.SUCCESS("✅ 30 doctors inserted successfully!"))
