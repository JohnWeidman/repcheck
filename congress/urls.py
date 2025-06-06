from django.urls import path
from .views import *

urlpatterns = [
   path("", congress, name="congress"),
   path("house/", house_not_home, name="house"),
   path("senate/", i_am_the_senate, name="senate"),
   path("detail/<int:pk>", details, name="detail")
]
