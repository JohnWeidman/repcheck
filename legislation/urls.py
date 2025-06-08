from django.urls import path
from .views import *

urlpatterns = [
    path("bills/", im_just_a_bill, name="bills"),
    path("laws/", laws, name="laws"),
    path("", legislation_landing_page, name="legislation_landing_page"),
    path("bill_detail/<int:congress>/<str:bill_type>/<str:bill_id>/", bill_detail, name="bill_detail"),
    path("law_detail/<int:law_id>/", law_detail, name="law_detail"),
]
