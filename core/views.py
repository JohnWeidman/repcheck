from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()
# Create your views here.

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"
CACHE_TIMEOUT = 60 * 10  # 10 minutes


@cache_page(CACHE_TIMEOUT)
def home(request):
    url = f"{BASE_URL}/bill?api_key={API_KEY}&limit=12"
    response = requests.get(url)
    if response.status_code == 200:
        bills = response.json().get("bills", [])
    else:
        bills = []

    context = {
        "bills": bills,
    }
    return render(request, "core/home.html", context)
