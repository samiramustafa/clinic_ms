from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework import viewsets,generics
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
  
# views.py

# ... (باقي الاستيرادات والكلاسات الأخرى مثل DoctorViewSet, PatientViewSet etc.)

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet للتعامل مع المستخدمين (CustomUser).
    يتضمن إنشاء المستخدمين، وعرض/تعديل بيانات المستخدم المسجل (`/me`).
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        يمكن تقييد الـ queryset هنا إذا لزم الأمر،
        مثلاً، إظهار المستخدمين للمدير فقط.
        """
        user = self.request.user
        if user.is_staff: # مثال: الأدمن يرى الكل
            return CustomUser.objects.all()
        elif user.is_authenticated: # المستخدم المسجل يرى نفسه فقط (عبر /me)
             # هذا الـ queryset الأساسي قد لا يُستخدم كثيراً بوجود /me
             # ولكن من الجيد تقييده
            return CustomUser.objects.filter(pk=user.pk)
        return CustomUser.objects.none() # غير المسجل لا يرى شيئاً


    def get_permissions(self):
        """
        تحديد الأذونات المطلوبة لكل action.
        """
        if self.action == "create":
            # السماح لأي شخص بإنشاء حساب جديد (تسجيل)
            return [AllowAny()]
        elif self.action == "me":
            # يجب أن يكون المستخدم مسجلاً للوصول إلى بياناته (/me)
            return [IsAuthenticated()]
        # يمكنك جعل باقي العمليات (list, retrieve, update, destroy) تتطلب IsAdminUser
        # return [permissions.IsAdminUser()]
        # أو تركها تتطلب IsAuthenticated إذا كان المستخدم يستطيع تعديل/حذف نفسه (لكن /me أفضل للتعديل)
        return [IsAuthenticated()] # القيمة الافتراضية الحالية

    def create(self, request, *args, **kwargs):
        """
        إنشاء مستخدم جديد.
        الـ UserSerializer المعدل سيتولى إنشاء البروفايل (Patient/Doctor) أيضاً.
        تمت إزالة التحقق اليدوي من العمر من هنا لأنه تم نقله لـ UserSerializer.
        """
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get', 'put'], permission_classes=[IsAuthenticated], url_path='me')
    def me(self, request):
        """
        Action مخصص لعرض (GET) أو تعديل (PUT) بيانات المستخدم المسجل حالياً وبروفايله.
        """
        user = request.user

        # --- GET Request: عرض بيانات المستخدم وبروفايله ---
        if request.method == 'GET':
            user_serializer = self.get_serializer(user)
            user_data = user_serializer.data

            # إضافة بيانات البروفايل بناءً على دور المستخدم
            if user.role == 'patient':
                try:
                    # استخدام related_name 'patient_profile' للوصول المباشر
                    patient_profile = user.patient_profile
                    patient_serializer = PatientSerializer(patient_profile)
                    user_data['patient_profile'] = patient_serializer.data
                except Patient.DoesNotExist:
                    user_data['patient_profile'] = None # البروفايل غير موجود
            elif user.role == 'doctor':
                try:
                     # استخدام related_name 'doctor_profile' للوصول المباشر
                    doctor_profile = user.doctor_profile
                    doctor_serializer = DoctorSerializer(doctor_profile)
                    user_data['doctor_profile'] = doctor_serializer.data
                except Doctor.DoesNotExist:
                    user_data['doctor_profile'] = None # البروفايل غير موجود
            # يمكنك إضافة elif user.role == 'admin': إذا كان للأدمن بروفايل خاص

            return Response(user_data, status=status.HTTP_200_OK)

        # --- PUT Request: تعديل بيانات المستخدم و/أو بروفايله ---
        elif request.method == 'PUT':
            # 1. تحديث بيانات المستخدم الأساسية (CustomUser)
            #    نستخدم partial=True للسماح بتحديث جزئي (مثلاً تغيير الاسم فقط)
            user_serializer = self.get_serializer(user, data=request.data, partial=True)
            try:
                user_serializer.is_valid(raise_exception=True)
            except serializers.ValidationError as e:
                 return Response({"user_errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)


            # 2. تحديث بيانات البروفايل (إذا تم إرسالها)
            profile_serializer = None
            profile_data_key = None
            profile_errors = None
            profile_updated = False

            if user.role == 'patient':
                profile_data_key = 'patient_profile' # المفتاح المتوقع من الفرونت
                if profile_data_key in request.data:
                    patient_data = request.data.get(profile_data_key)
                    if isinstance(patient_data, dict): # التأكد من أنه قاموس
                        try:
                            patient_profile = user.patient_profile
                            profile_serializer = PatientSerializer(patient_profile, data=patient_data, partial=True)
                        except Patient.DoesNotExist:
                             profile_errors = {"detail": "Patient profile not found for this user."}
                    else:
                        profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}

            elif user.role == 'doctor':
                profile_data_key = 'doctor_profile' # المفتاح المتوقع من الفرونت
                if profile_data_key in request.data:
                    doctor_data = request.data.get(profile_data_key)
                    if isinstance(doctor_data, dict):
                        try:
                            doctor_profile = user.doctor_profile
                            profile_serializer = DoctorSerializer(doctor_profile, data=doctor_data, partial=True)
                        except Doctor.DoesNotExist:
                             profile_errors = {"detail": "Doctor profile not found for this user."}
                    else:
                         profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}


            # التحقق من صحة بيانات البروفايل إذا تم تقديمها
            if profile_serializer:
                try:
                    profile_serializer.is_valid(raise_exception=True)
                    profile_updated = True # جاهز للحفظ
                except serializers.ValidationError as e:
                    # جمع أخطاء البروفايل
                    profile_errors = e.detail


            # 3. التعامل مع النتائج والحفظ
            if profile_errors:
                # إذا كان هناك خطأ في بيانات البروفايل، أرجع الخطأ فوراً
                 # يمكنك دمجها مع أخطاء المستخدم إذا أردت
                return Response({f"{profile_data_key}_errors": profile_errors}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # إذا كانت بيانات المستخدم والبروفايل (إذا قُدم) صالحة
                # احفظ بيانات المستخدم الأساسية أولاً
                user_serializer.save()

                # احفظ بيانات البروفايل إذا تم تحديثها بنجاح
                if profile_updated and profile_serializer:
                    profile_serializer.save()

                # أرجع بيانات المستخدم المحدثة مع بيانات البروفايل المحدثة
                final_response_data = user_serializer.data # بيانات المستخدم الأساسية المحدثة
                if profile_updated and user.role == 'patient':
                     # أعد تحميل بيانات البروفايل بعد الحفظ للتأكد من أنها محدثة
                    final_response_data['patient_profile'] = PatientSerializer(user.patient_profile).data
                elif profile_updated and user.role == 'doctor':
                    final_response_data['doctor_profile'] = DoctorSerializer(user.doctor_profile).data
                elif user.role == 'patient': # إذا لم يتم تحديث البروفايل ولكن المستخدم مريض
                    try: final_response_data['patient_profile'] = PatientSerializer(user.patient_profile).data
                    except Patient.DoesNotExist: final_response_data['patient_profile'] = None
                elif user.role == 'doctor': # إذا لم يتم تحديث البروفايل ولكن المستخدم طبيب
                     try: final_response_data['doctor_profile'] = DoctorSerializer(user.doctor_profile).data
                     except Doctor.DoesNotExist: final_response_data['doctor_profile'] = None


                return Response(final_response_data, status=status.HTTP_200_OK)


# ... (باقي الـ Views الأخرى في الملف مثل CityViewSet, AreaListView, Login_view etc.)                   
# class UserViewSet(viewsets.ModelViewSet):
#     queryset = CustomUser.objects.all()
#     serializer_class = UserSerializer
    
#     def create(self, request, *args, **kwargs):
#         """Custom create method to add extra validation"""
#         data = request.data

#         patient_ser = PatientSerializer(data=data)

#         try:
#             patient_ser.validate_birth_date(data.get('date_of_birth'))
#         except ValidationError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


#         # Call default create method
#         return super().create(request, *args, **kwargs)

#     def get_permissions(self):
#         if self.action == "create":  # السماح بتسجيل مستخدم جديد بدون توثيق
#             return [AllowAny()]
#         return [IsAuthenticated()]  # باقي العمليات تتطلب توثيق

#     @action(detail=False, methods=['get', 'put'])
#     def me(self, request):
#         try:
#             user = request.user

#             if not user.is_authenticated:
#                 return Response({"detail": "Authentication credentials were not provided."}, status=401)
#             if request.method == "GET":
#                 serializer = self.get_serializer(user)
#                 patient = get_object_or_404(Patient, user=user) 
#                 patient_serializer = PatientSerializer(patient)
#                 user_data = serializer.data
#                 user_data['patient_data'] = patient_serializer.data
#                 return Response(data=user_data)

#             elif request.method == "PUT":
#                 serializer = self.get_serializer(user, data=request.data, partial=True)
                
#                 if user.role=="patient":
#                     print("User is a patient")                     
#                     patient_data = request.data.get('patient_data')
#                     patient_data['user'] = user.id
#                     patient = get_object_or_404(Patient, user=user)
#                     print("before")
#                     required_fields = PatientSerializer().get_fields()
#                     print("Required fields:", required_fields) 
#                     patient_serializer = PatientSerializer(patient, data=patient_data, partial=True)
#                     print(patient_serializer)
#                     if patient_serializer.is_valid():
#                         print("inside if")
#                         patient_serializer.save()
#                         serializer.save()
#                         return Response(serializer.data)
#                     else:
#                         print("Patient serializer errors:", patient_serializer.errors)
#                         print("inside else")
#                         return Response({"error": "Invalid patient data", "details": patient_serializer.errors}, status=400)

#                     #
#                 if serializer.is_valid():
#                     serializer.save()
#                     return Response(serializer.data)
#                 return Response(serializer.errors, status=400)

#         except :
#             return Response({"error": "An error occurred."})

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    
class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    
class AreaListView(ListAPIView):
    serializer_class = AreaSerializer

    def get_queryset(self):
        city_id = self.request.GET.get("city")
        if city_id:
            return Area.objects.filter(city_id=city_id)
        return Area.objects.all()

@api_view(["POST"])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user:
        return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
    return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)



class AvailableTimeListCreateView(APIView):
    """Handles listing all available times and creating new ones."""
    
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        doctor_id = request.query_params.get("doctor_id")
        if doctor_id:
            available_times = AvailableTime.objects.filter(doctor_id=doctor_id)
        else:
            available_times = AvailableTime.objects.all()

        serializer = AvailableTimeSerializer(available_times, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AvailableTimeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvailableTimeDetailView(APIView):
    """Handles retrieving, updating, and deleting specific available times."""
    
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        available_time = get_object_or_404(AvailableTime, pk=pk)
        serializer = AvailableTimeSerializer(available_time)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        available_time = get_object_or_404(AvailableTime, pk=pk)
        serializer = AvailableTimeSerializer(available_time, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        available_time = get_object_or_404(AvailableTime, pk=pk)
        available_time.delete()
        return Response({"message": "Available time deleted successfully"}, status=status.HTTP_204_NO_CONTENT)







#=======appointments================

class AppointmentListCreateView(APIView):
    def get(self, request):
        doctor_id = request.GET.get("doctor_id")

        if doctor_id:
            appointments = Appointment.objects.filter(doctor_id=doctor_id)
        else:
            appointments = Appointment.objects.all()

        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        doctor_id = request.data.get("doctor")
        available_time_id = request.data.get("available_time")

        # التحقق من أن available_time يخص الطبيب المحدد
        available_time = get_object_or_404(AvailableTime, id=available_time_id)
        if available_time.doctor.id != int(doctor_id):
            return Response(
                {"error": "The selected available time does not belong to the chosen doctor."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentDetailView(APIView):
    def get(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        serializer = AppointmentSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.delete()
        return Response({"message": "Appointment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



#  feedback
class FeedbackListCreateView(APIView):
    def get(self, request):
        doctor_id = request.GET.get("doctor_id")

        if doctor_id:
            feedbacks = Feedback.objects.filter(doctor_id=doctor_id)
        else:
            feedbacks = Feedback.objects.all()

        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            serializer.instance.doctor.update_rating()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class FeedbackDetailView(APIView):
    def get(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        serializer = FeedbackSerializer(feedback)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        serializer = FeedbackSerializer(feedback, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            serializer.instance.doctor.update_rating()
        
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        doctor = feedback.doctor
        feedback.delete()
        doctor.update_rating()
        return Response({"message": "Feedback deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


