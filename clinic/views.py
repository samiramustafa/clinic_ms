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
from .permissions import IsAdminRole # استيراد الصلاحية المخصصة
# views.py

# ... (باقي الاستيرادات والكلاسات الأخرى مثل DoctorViewSet, PatientViewSet etc.)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet للتعامل مع المستخدمين (CustomUser).
    يتضمن إنشاء المستخدمين، وعرض/تعديل بيانات المستخدم المسجل (`/me`).
    """
    queryset = CustomUser.objects.all()
    #serializer_class = UserSerializer # Keep commented if using get_serializer_class

    # --- 👇 بداية الدوال على مستوى الكلاس ---
    def get_serializer_class(self):
        if self.action == 'list' and self.request.user.is_authenticated and self.request.user.role == 'admin':
             return AdminUserSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if self.action == 'list':
            if user.is_authenticated and user.role == 'admin':
                return CustomUser.objects.all().order_by('-date_joined')
            else:
                return CustomUser.objects.none()
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'me']:
             if user.is_authenticated:
                  if self.action == 'me':
                      # Note: 'me' is detail=False, it doesn't use get_object/queryset filtering by pk.
                      # It operates directly on request.user. So returning all() is fine here too,
                      # or just filter by user.pk for consistency, but it won't affect 'me' action directly.
                      return CustomUser.objects.filter(pk=user.pk) # Let's keep this for safety if 'me' logic changes
                  # For other detail actions (retrieve, update, destroy)
                  return CustomUser.objects.all()
        # Fallback or for 'create' action etc.
        return CustomUser.objects.all()

    # --- 👇 الدوال الأخرى الآن على نفس مستوى get_queryset ---
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        if instance == user:
            return Response({"detail": "Admins cannot delete their own account."}, status=status.HTTP_403_FORBIDDEN)
        if instance.is_superuser:
            return Response({"detail": "Superusers cannot be deleted."}, status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action in ['list', 'destroy', 'retrieve' ,'partial_update', 'update']:
            return [IsAdminRole()]
        elif self.action == 'create':
            return [AllowAny()]
        elif self.action == 'me':
            # 'me' action itself checks IsAuthenticated via decorator, but doesn't hurt to double check
            return [permissions.IsAuthenticated()]
        # Default permissions for any other potential actions
        return [permissions.IsAuthenticated()] # Or more restrictive if needed

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        new_active_status = serializer.validated_data.get('is_active', instance.is_active)
        # Use validated_data which is available after is_valid() call in update/partial_update
        # Check if the field was actually included in the request data for partial updates
        if 'is_active' in serializer.validated_data:
             if instance == user and not new_active_status:
                  raise serializers.ValidationError({"is_active": "Admins cannot deactivate their own account."})
             if instance.is_superuser and not new_active_status:
                  raise serializers.ValidationError({"is_active": "Superuser account cannot be deactivated."})
        serializer.save()

    @action(detail=False, methods=['get', 'put'], permission_classes=[IsAuthenticated], url_path='me')
    def me(self, request):
        user = request.user # The user making the request

        if request.method == 'GET':
            # Pass the authenticated user directly to the serializer
            serializer = self.get_serializer(user) # Use the correct serializer (UserSerializer)
            user_data = serializer.data
             # Add nested profile data
            if user.role == 'patient':
                try:
                    patient_profile = user.patient_profile
                    # Use the appropriate serializer for the profile
                    patient_serializer = PatientSerializer(patient_profile)
                    user_data['patient_profile'] = patient_serializer.data
                except Patient.DoesNotExist:
                    user_data['patient_profile'] = None
            elif user.role == 'doctor':
                 try:
                    doctor_profile = user.doctor_profile
                    # Use the appropriate serializer for the profile
                    doctor_serializer = DoctorSerializer(doctor_profile) # Make sure DoctorSerializer is defined correctly
                    user_data['doctor_profile'] = doctor_serializer.data
                 except Doctor.DoesNotExist:
                    user_data['doctor_profile'] = None
            return Response(user_data) # No need for status=status.HTTP_200_OK explicitly

        elif request.method == 'PUT':
             # Use partial=True for PUT as well to allow partial updates easily
             user_serializer = self.get_serializer(user, data=request.data, partial=True)
             try:
                 user_serializer.is_valid(raise_exception=True)
             except serializers.ValidationError as e:
                  # Return specific validation errors
                  return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

             profile_serializer = None
             profile_data_key = None
             profile_errors = None
             profile_updated = False

             # Logic to handle nested patient_profile update
             if user.role == 'patient':
                  profile_data_key = 'patient_profile'
                  if profile_data_key in request.data:
                     patient_data = request.data.get(profile_data_key)
                     if isinstance(patient_data, dict):
                         try:
                             patient_profile = user.patient_profile
                             # Ensure PatientSerializer allows partial updates
                             profile_serializer = PatientSerializer(patient_profile, data=patient_data, partial=True)
                         except Patient.DoesNotExist:
                              profile_errors = {"detail": "Patient profile not found for this user."}
                     else:
                         profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}

             # Logic to handle nested doctor_profile update
             elif user.role == 'doctor':
                  profile_data_key = 'doctor_profile'
                  if profile_data_key in request.data:
                      doctor_data = request.data.get(profile_data_key)
                      if isinstance(doctor_data, dict):
                           try:
                               doctor_profile = user.doctor_profile
                               # Ensure DoctorSerializer allows partial updates (it might be read-only now)
                               # You might need a different serializer for updating the doctor profile via 'me'
                               # Or adjust DoctorSerializer to handle updates if needed elsewhere
                               profile_serializer = DoctorSerializer(doctor_profile, data=doctor_data, partial=True) # Adjust if DoctorSerializer is read-only
                           except Doctor.DoesNotExist:
                                profile_errors = {"detail": "Doctor profile not found for this user."}
                      else:
                           profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}


             if profile_serializer:
                 try:
                     profile_serializer.is_valid(raise_exception=True)
                     profile_updated = True
                 except serializers.ValidationError as e:
                     profile_errors = e.detail # Collect profile validation errors

             # Check for errors before saving
             if profile_errors:
                  # Combine errors if necessary or return profile errors separately
                  return Response({f"{profile_data_key}_errors": profile_errors}, status=status.HTTP_400_BAD_REQUEST)
             else:
                  # Save user data first
                  user_instance = user_serializer.save()

                  # Save profile data if updated
                  if profile_updated and profile_serializer:
                      profile_serializer.save()

                  # Return updated data (re-serialize the instance after save)
                  final_serializer = self.get_serializer(user_instance) # Re-serialize the user
                  final_response_data = final_serializer.data
                   # Add updated profile data back
                  if user.role == 'patient':
                     try: final_response_data['patient_profile'] = PatientSerializer(user_instance.patient_profile).data
                     except Patient.DoesNotExist: final_response_data['patient_profile'] = None
                  elif user.role == 'doctor':
                      try: final_response_data['doctor_profile'] = DoctorSerializer(user_instance.doctor_profile).data
                      except Doctor.DoesNotExist: final_response_data['doctor_profile'] = None

                  return Response(final_response_data)

# class UserViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet للتعامل مع المستخدمين (CustomUser).
#     يتضمن إنشاء المستخدمين، وعرض/تعديل بيانات المستخدم المسجل (`/me`).
#     """
#     queryset = CustomUser.objects.all()
#     #serializer_class = UserSerializer
#     def get_serializer_class(self):
#         # استخدام سيريالايزر مختلف للأدمن عند عرض القائمة
#         if self.action == 'list' and self.request.user.is_authenticated and self.request.user.role == 'admin':
#              return AdminUserSerializer
#         # استخدام السيريالايزر العادي للباقي (مثل /me والتسجيل)
#         return UserSerializer
# # In clinic/views.py -> UserViewSet

# def get_queryset(self):
#     """
#     تحديد الـ QuerySet بناءً على الـ action ودور المستخدم.
#     """
#     user = self.request.user

#     # --- حالة عرض القائمة ---
#     if self.action == 'list':
#         if user.is_authenticated and user.role == 'admin':
#             # الأدمن يرى كل المستخدمين
#             return CustomUser.objects.all().order_by('-date_joined')
#         else:
#             # غير الأدمن لا يرى القائمة
#             return CustomUser.objects.none()

#     # --- حالة العمليات على كائن محدد (retrieve, update, partial_update, destroy) ---
#     # أو أي action آخر يتطلب get_object()
#     # يجب أن نُرجع الـ queryset الأساسي للسماح لـ get_object() بالعثور على الكائن
#     # بناءً على الـ pk الموجود في الـ URL.
#     # الصلاحيات (get_permissions) ستحدد ما إذا كان الإجراء مسموحًا به أم لا.
#     # أيضًا، صلاحيات الكائن (object-level permissions) يمكن إضافتها لاحقًا إذا لزم الأمر.
#     elif self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'me']: # أضف 'me' هنا أيضًا
#          # إذا كان المستخدم مسجل الدخول، اسمح برؤية أي مستخدم مبدئيًا
#          # (الصلاحيات ستحدد الباقي)
#          # أو على الأقل بياناته هو لـ 'me'
#          if user.is_authenticated:
#               # لـ 'me'، نحتاج فقط لبيانات المستخدم الحالي
#               if self.action == 'me':
#                   return CustomUser.objects.filter(pk=user.pk)
#               # لباقي العمليات التي تحتاج get_object (retrieve, update, destroy)
#               # يجب أن نرجع QuerySet يحتوي على *كل* المستخدمين المحتملين
#               # الذين قد يعمل عليهم الأدمن.
#               # في حالتنا، الأدمن يمكنه العمل على أي مستخدم، لذا نرجع الكل.
#               return CustomUser.objects.all() # <-- التغيير الرئيسي هنا

#     # --- الحالات الأخرى (مثل create أو إذا لم يكن مسجل الدخول للعمليات المحمية) ---
#     # يمكن إرجاع queryset فارغ أو الاعتماد على طبقة الصلاحيات
#     # إرجاع الـ queryset الأصلي هنا آمن لأن الصلاحيات ستمنع الوصول غير المصرح به
#     # return self.queryset # self.queryset هو CustomUser.objects.all()
#     return CustomUser.objects.all() # أو هذا، نفس النتيجة
#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object() # المستخدم المراد حذفه
#         user = request.user        # الأدمن الذي يقوم بالطلب

#         # --- منع حذف الأدمن لنفسه ---
#         if instance == user:
#             return Response({"detail": "Admins cannot delete their own account."},
#                             status=status.HTTP_403_FORBIDDEN)

#         # --- (اختياري) منع حذف أي مستخدم خارق ---
#         if instance.is_superuser:
#             return Response({"detail": "Superusers cannot be deleted."},
#                             status=status.HTTP_403_FORBIDDEN)

#         # --- (اختياري) منع حذف الأدمن لمستخدم أدمن آخر (إذا أردت) ---
#         # if instance.role == 'admin' and not user.is_superuser: # اسمح فقط للسوبر يوزر بحذف الأدمن الآخرين
#         #     return Response({"detail": "You do not have permission to delete other admin users."},
#         #                    status=status.HTTP_403_FORBIDDEN)

#         # --- إذا مرت كل التحققات، استمر في الحذف العادي ---
#         self.perform_destroy(instance)
#         return Response(status=status.HTTP_204_NO_CONTENT)

# # لا تنسَ دالة perform_destroy القياسية (موجودة ضمنياً في ModelViewSet)
# # def perform_destroy(self, instance):
# #     instance.delete()
#     def get_permissions(self):
#            # تحديد الأذونات لكل action
#         if self.action in ['list', 'destroy', 'retrieve' ,'partial_update', 'update']: # الأدمن فقط يمكنه عرض القائمة، حذف مستخدم، أو عرض تفاصيل أي مستخدم
#             # لاحظ: retrieve هنا يعني /api/users/{user_id}/
#             # قد ترغب في تقييده أكثر إذا كان الأدمن لا يجب أن يرى تفاصيل كل مستخدم عبر هذا المسار
#             return [IsAdminRole()]
#         elif self.action == 'create':
#             return [AllowAny()] # السماح بالتسجيل للجميع
#         elif self.action == 'me':
#             return [permissions.IsAuthenticated()] # المستخدم المسجل يصل لبياناته
#         # update, partial_update يجب أن تتم عبر /me أو بواسطة الأدمن
#         # حالياً هي محمية بـ IsAuthenticated افتراضيًا، قد تحتاج لـ IsAdminRole هنا أيضاً إذا أردت السماح للأدمن بالتعديل
#         return [permissions.IsAuthenticated()]
#     def create(self, request, *args, **kwargs):
#         """
#         إنشاء مستخدم جديد.
#         الـ UserSerializer المعدل سيتولى إنشاء البروفايل (Patient/Doctor) أيضاً.
#         تمت إزالة التحقق اليدوي من العمر من هنا لأنه تم نقله لـ UserSerializer.
#         """
#         return super().create(request, *args, **kwargs)
#     def perform_update(self, serializer):
#         instance = serializer.instance # المستخدم الذي يتم تعديله
#         user = self.request.user      # الأدمن الذي يقوم بالطلب
#         new_active_status = serializer.validated_data.get('is_active', instance.is_active)

#         # --- منع تعطيل الأدمن لنفسه ---
#         if instance == user and not new_active_status:
#             # يمكنك رفع ValidationError أو إرجاع استجابة خطأ مباشرة
#             # هذا يتطلب تعديل بسيط لكيفية عمل perform_update القياسية
#             # أو يمكنك وضع هذا التحقق في دالة update/partial_update نفسها
#             raise serializers.ValidationError("Admins cannot deactivate their own account.")

#         # --- (اختياري) منع تعطيل السوبر يوزر ---
#         if instance.is_superuser and not new_active_status:
#             raise serializers.ValidationError("Superuser account cannot be deactivated.")

#         # --- (اختياري) منع تعطيل الأدمن لأدمن آخر (إذا لم يكن سوبر يوزر) ---
#         # if instance.role == 'admin' and not new_active_status and not user.is_superuser:
#         #     raise serializers.ValidationError("You cannot deactivate other admin accounts.")

#         serializer.save()
#     @action(detail=False, methods=['get', 'put'], permission_classes=[IsAuthenticated], url_path='me')
#     def me(self, request):
#         """
#         Action مخصص لعرض (GET) أو تعديل (PUT) بيانات المستخدم المسجل حالياً وبروفايله.
#         """
#         user = request.user

#         # --- GET Request: عرض بيانات المستخدم وبروفايله ---
#         if request.method == 'GET':
#             user_serializer = self.get_serializer(user)
#             user_data = user_serializer.data

#             # إضافة بيانات البروفايل بناءً على دور المستخدم
#             if user.role == 'patient':
#                 try:
#                     # استخدام related_name 'patient_profile' للوصول المباشر
#                     patient_profile = user.patient_profile
#                     patient_serializer = PatientSerializer(patient_profile)
#                     user_data['patient_profile'] = patient_serializer.data
#                 except Patient.DoesNotExist:
#                     user_data['patient_profile'] = None # البروفايل غير موجود
#             elif user.role == 'doctor':
#                 try:
#                      # استخدام related_name 'doctor_profile' للوصول المباشر
#                     doctor_profile = user.doctor_profile
#                     doctor_serializer = DoctorSerializer(doctor_profile)
#                     user_data['doctor_profile'] = doctor_serializer.data
#                 except Doctor.DoesNotExist:
#                     user_data['doctor_profile'] = None # البروفايل غير موجود
#             # يمكنك إضافة elif user.role == 'admin': إذا كان للأدمن بروفايل خاص

#             return Response(user_data, status=status.HTTP_200_OK)

#         # --- PUT Request: تعديل بيانات المستخدم و/أو بروفايله ---
#         elif request.method == 'PUT':
#             # 1. تحديث بيانات المستخدم الأساسية (CustomUser)
#             #    نستخدم partial=True للسماح بتحديث جزئي (مثلاً تغيير الاسم فقط)
#             user_serializer = self.get_serializer(user, data=request.data, partial=True)
#             try:
#                 user_serializer.is_valid(raise_exception=True)
#             except serializers.ValidationError as e:
#                  return Response({"user_errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)


#             # 2. تحديث بيانات البروفايل (إذا تم إرسالها)
#             profile_serializer = None
#             profile_data_key = None
#             profile_errors = None
#             profile_updated = False

#             if user.role == 'patient':
#                 profile_data_key = 'patient_profile' # المفتاح المتوقع من الفرونت
#                 if profile_data_key in request.data:
#                     patient_data = request.data.get(profile_data_key)
#                     if isinstance(patient_data, dict): # التأكد من أنه قاموس
#                         try:
#                             patient_profile = user.patient_profile
#                             profile_serializer = PatientSerializer(patient_profile, data=patient_data, partial=True)
#                         except Patient.DoesNotExist:
#                              profile_errors = {"detail": "Patient profile not found for this user."}
#                     else:
#                         profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}

#             elif user.role == 'doctor':
#                 profile_data_key = 'doctor_profile' # المفتاح المتوقع من الفرونت
#                 if profile_data_key in request.data:
#                     doctor_data = request.data.get(profile_data_key)
#                     if isinstance(doctor_data, dict):
#                         try:
#                             doctor_profile = user.doctor_profile
#                             profile_serializer = DoctorSerializer(doctor_profile, data=doctor_data, partial=True)
#                         except Doctor.DoesNotExist:
#                              profile_errors = {"detail": "Doctor profile not found for this user."}
#                     else:
#                          profile_errors = {"detail": f"'{profile_data_key}' data must be an object/dictionary."}


#             # التحقق من صحة بيانات البروفايل إذا تم تقديمها
#             if profile_serializer:
#                 try:
#                     profile_serializer.is_valid(raise_exception=True)
#                     profile_updated = True # جاهز للحفظ
#                 except serializers.ValidationError as e:
#                     # جمع أخطاء البروفايل
#                     profile_errors = e.detail


#             # 3. التعامل مع النتائج والحفظ
#             if profile_errors:
#                 # إذا كان هناك خطأ في بيانات البروفايل، أرجع الخطأ فوراً
#                  # يمكنك دمجها مع أخطاء المستخدم إذا أردت
#                 return Response({f"{profile_data_key}_errors": profile_errors}, status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 # إذا كانت بيانات المستخدم والبروفايل (إذا قُدم) صالحة
#                 # احفظ بيانات المستخدم الأساسية أولاً
#                 user_serializer.save()

#                 # احفظ بيانات البروفايل إذا تم تحديثها بنجاح
#                 if profile_updated and profile_serializer:
#                     profile_serializer.save()

#                 # أرجع بيانات المستخدم المحدثة مع بيانات البروفايل المحدثة
#                 final_response_data = user_serializer.data # بيانات المستخدم الأساسية المحدثة
#                 if profile_updated and user.role == 'patient':
#                      # أعد تحميل بيانات البروفايل بعد الحفظ للتأكد من أنها محدثة
#                     final_response_data['patient_profile'] = PatientSerializer(user.patient_profile).data
#                 elif profile_updated and user.role == 'doctor':
#                     final_response_data['doctor_profile'] = DoctorSerializer(user.doctor_profile).data
#                 elif user.role == 'patient': # إذا لم يتم تحديث البروفايل ولكن المستخدم مريض
#                     try: final_response_data['patient_profile'] = PatientSerializer(user.patient_profile).data
#                     except Patient.DoesNotExist: final_response_data['patient_profile'] = None
#                 elif user.role == 'doctor': # إذا لم يتم تحديث البروفايل ولكن المستخدم طبيب
#                      try: final_response_data['doctor_profile'] = DoctorSerializer(user.doctor_profile).data
#                      except Doctor.DoesNotExist: final_response_data['doctor_profile'] = None


#                 return Response(final_response_data, status=status.HTTP_200_OK)




class DoctorViewSet(viewsets.ReadOnlyModelViewSet): # <--- To this (Safer for public access)
    """
    API endpoint that allows PUBLIC viewing of doctors list and details.
    Uses prefetching for optimization.
    """
    # --- استخدم السيريالايزر المعدل ---
    serializer_class = DoctorSerializer

    # --- اسمح لأي شخص بالوصول (للقراءة فقط بسبب ReadOnlyModelViewSet) ---
    permission_classes = [AllowAny]

    # --- Queryset محسن باستخدام select_related ---
    queryset = Doctor.objects.select_related(
        'user',         # Fetch related CustomUser
        'user__city',   # Fetch related City through CustomUser
        'user__area'  # Fetch related Area through CustomUser
    ).all()
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
        data = request.data.copy()

        # لو المستخدم مسجل ومفيش patient جاي من الفورم، نستخدم الحالي
        if not data.get("patient"):
            try:
                patient = Patient.objects.get(user=request.user)
                data["patient"] = patient.id
            except Patient.DoesNotExist:
                return Response(
                    {"detail": "Patient profile not found for this user."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = AppointmentSerializer(data=data)

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
        ordering = request.GET.get("ordering", "-created_at")

        allowed_ordering_fields = ["created_at", "-created_at", "rate", "-rate"]

        if ordering not in allowed_ordering_fields:
            ordering = "-created_at"  

        if doctor_id:
            feedbacks = Feedback.objects.filter(doctor_id=doctor_id)
        else:
            feedbacks = Feedback.objects.all()

        feedbacks = feedbacks.order_by(ordering)

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

class AdminTokenObtainPairView(TokenObtainPairView):
    """
    Login endpoint specifically for admin users.
    Returns JWT tokens only if the user has role='admin'.
    """
    serializer_class = AdminTokenObtainPairSerializer
    permission_classes = [AllowAny] # 


class AdminFeedbackListView(generics.ListAPIView):
    """
    Admin view to list all feedbacks.
    Allows filtering by is_active status.
    """
    serializer_class = FeedbackSerializer
    permission_classes = [IsAdminRole] # فقط الأدمن يمكنه الوصول

    def get_queryset(self):
        queryset = Feedback.objects.select_related('patient__user', 'doctor__user').all().order_by('-created_at')
        is_active_filter = self.request.query_params.get('is_active')
        if is_active_filter is not None:
             if is_active_filter.lower() == 'true':
                 queryset = queryset.filter(is_active=True)
             elif is_active_filter.lower() == 'false':
                 queryset = queryset.filter(is_active=False)
        return queryset

# In clinic/views.py

# --- 👇 تغيير هنا ---
class AdminFeedbackDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin view to retrieve, update, and delete a specific feedback entry.
    Allows admin to change 'is_active', 'feedback', 'rate', and 'admin_notes'.
    """
    # --- 👇 تأكد أن السيريالايزر يسمح بالكتابة لهذه الحقول ---
    serializer_class = FeedbackSerializer
    permission_classes = [IsAdminRole] # فقط الأدمن يمكنه الوصول
    queryset = Feedback.objects.all()

    # --- 👇 override perform_update و perform_destroy لتحديث تقييم الطبيب ---
    def perform_update(self, serializer):
        # استدعاء الحفظ العادي أولاً
        instance = serializer.save()
        # تحديث تقييم الطبيب بعد التعديل (خاصة إذا تم تعديل الـ rate)
        if instance.doctor:
             instance.doctor.update_rating() # افترض وجود هذه الدالة في موديل Doctor

    def perform_destroy(self, instance):
        doctor = instance.doctor # احصل على الطبيب قبل الحذف
        instance.delete()
        # تحديث تقييم الطبيب بعد الحذف
        if doctor:
             doctor.update_rating()
