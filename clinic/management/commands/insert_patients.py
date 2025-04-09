from django.core.management.base import BaseCommand
from clinic.models import CustomUser, Patient

class Command(BaseCommand):
    help = 'Insert 3 static patients'

    def handle(self, *args, **kwargs):
        users_data = [
            {
                'first_name': 'Assem',
                'last_name': 'Ali',
                'username': 'assemali_101',
                'full_name': 'Assem Ali',
                'phone_number': '01012345678',
                'role': 'patient',
                'city_id': 1,
                'area_id': 1,
                'national_id': '12345678901234',
            },
            {
                'first_name': 'Sara',
                'last_name': 'Kamel',
                'username': 'sarakamel_102',
                'full_name': 'Sara Kamel',
                'phone_number': '01123456789',
                'role': 'patient',
                'city_id': 2,
                'area_id': 2,
                'national_id': '23456789012345',
            },
            {
                'first_name': 'Ahmed',
                'last_name': 'Mansour',
                'username': 'ahmedmansour_103',
                'full_name': 'Ahmed Mansour',
                'phone_number': '01234567890',
                'role': 'patient',
                'city_id': 3,
                'area_id': 3,
                'national_id': '34567890123456',
            }
        ]

        for user_data in users_data:
            user = CustomUser.objects.create(
                username=user_data['username'],
                full_name=user_data['full_name'],
                phone_number=user_data['phone_number'],
                role=user_data['role'],
                city_id=user_data['city_id'],
                area_id=user_data['area_id'],
                national_id=user_data['national_id'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )

            Patient.objects.create(user=user)

        self.stdout.write(self.style.SUCCESS("✅ 3 static patients inserted successfully!"))
