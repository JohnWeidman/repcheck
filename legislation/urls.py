from django.urls import path
from .views import *

urlpatterns = [
    path("bills/", im_just_a_bill, name="bills"),
    path("laws/", laws, name="laws"),
    path("", legislation_landing_page, name="legislation_landing_page"),
]