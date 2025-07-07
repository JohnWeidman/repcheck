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

@cache_page(10)  # Cache for 15 minutes
def home(request):
    current_time = time.strftime("%Y-%m-%d %H:%M: %S")
    url = f"{BASE_URL}/bill?api_key={API_KEY}&limit=12"
    response = requests.get(url)
    if response.status_code == 200:
        bills = response.json().get("bills", [])
    else:
        bills = []
        
    context = {
        "bills": bills,
        "current_time": current_time,
    }
    return render(request, "core/home.html", context)