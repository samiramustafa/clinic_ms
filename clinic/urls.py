from django.urls import path
from .views import *

from clinic import views

urlpatterns = [
    path('all', views.index, name='index'),
]