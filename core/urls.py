from django.urls import path
from .views import *

urlpatterns = [
   path("", home, name="landing_page"),
   path("search/", search_page, name="search_page"),
]
