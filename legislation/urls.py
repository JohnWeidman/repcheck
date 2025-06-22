from django.urls import path
from .views import *

urlpatterns = [
    path("bills/", im_just_a_bill, name="bills"),
    path("bill-details-htmx/", bill_details_htmx, name="bill_details_htmx"),  # New HTMX endpoint
    path("laws/", laws, name="laws"),
    path("", legislation_landing_page, name="legislation_landing_page"),
]