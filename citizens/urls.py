from django.urls import path
from .views import citizen_home

urlpatterns = [
   path("/", citizen_home, name="home"),
]
