from django.core.management.base import BaseCommand
from clinic.models import City, Area  # تأكد أن لديك موديلات City و Area داخل models.py

CITIES_AREAS = {
    "Cairo": ["Nasr City", "Heliopolis", "Maadi", "Zamalek", "Shubra", "Downtown", "New Cairo", "Fifth Settlement"],
    "Giza": ["Dokki", "Mohandessin", "6th October", "Sheikh Zayed", "Haram", "Faisal", "Imbaba"],
    "Alexandria": ["Smouha", "Montazah", "Sidi Gaber", "Miami", "Stanley", "Bolkly", "Gleem"],
    "Sharqia": ["Zagazig", "Belbes", "Abu Kabir", "Minya al-Qamh", "Husseiniya", "Faqous"],
    "Dakahlia": ["Mansoura", "Mit Ghamr", "Talkha", "Belqas", "Sherbin", "Aga"],
    "Beheira": ["Damanhour", "Kafr El Dawwar", "Rashid", "Edko"],
    "Menoufia": ["Shibin El Kom", "Sadat City", "Menouf", "Ashmoun"],
    "Kafr El Sheikh": ["Kafr El Sheikh", "Desouk", "Baltim", "Metoubes"],
    "Fayoum": ["Fayoum City", "Ibshaway", "Sinnuris", "Tamiya"],
    "Beni Suef": ["Beni Suef", "Al Wasta", "Nasser", "Biba"],
    "Minya": ["Minya City", "Samalut", "Maghagha", "Mallawi"],
    "Asyut": ["Asyut City", "Abnub", "Dayrout", "Manfalut"],
    "Sohag": ["Sohag City", "Akhmim", "Tahta", "Juhayna"],
    "Qena": ["Qena City", "Nag Hammadi", "Dishna", "Luxor"],
    "Luxor": ["Luxor City", "Karnak", "Esna"],
    "Aswan": ["Aswan City", "Kom Ombo", "Edfu", "Abu Simbel"],
    "Red Sea": ["Hurghada", "Marsa Alam", "Safaga", "Quseir"],
    "Suez": ["Suez City", "Ain Sokhna", "Alganayen"],
    "Ismailia": ["Ismailia City", "Fayed", "Tell el Kebir"],
    "Port Said": ["Port Said City", "Dawahy", "Sharq"],
    "North Sinai": ["Arish", "Sheikh Zuweid", "Rafah"],
    "South Sinai": ["Sharm El Sheikh", "Dahab", "Nuweiba", "Saint Catherine"],
    "Matrouh": ["Marsa Matrouh", "Siwa", "El Salloum", "El Dabaa"],
    "New Valley": ["Kharga", "Dakhla", "Farafra"],
}

class Command(BaseCommand):
    help = "Load all Egyptian cities and their areas into the database"

    def handle(self, *args, **kwargs):
        for city_name, areas in CITIES_AREAS.items():
            city, created = City.objects.get_or_create(name=city_name)
            for area_name in areas:
                Area.objects.get_or_create(name=area_name, city=city)

        self.stdout.write(self.style.SUCCESS("✅ Successfully loaded all Egyptian cities and areas!"))
