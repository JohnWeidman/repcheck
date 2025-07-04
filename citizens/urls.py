from django.urls import path
from .views import *

urlpatterns = [
   path("", citizen_home, name="home"),
   path("resources/", citizen_resources, name="citizen_resources"),
]
