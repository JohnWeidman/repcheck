from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.core.cache import cache

from dotenv import load_dotenv
from celery import shared_task

import requests
import os
import time
import hashlib
import json

load_dotenv()
# Create your views here.

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"
CACHE_TIMEOUT = 60 * 15  # 10 minutes


@shared_task
def update_bills_cache():
    url = f"{BASE_URL}/bill?api_key={API_KEY}&limit=12"
    response = requests.get(url)
    
    if response.status_code == 200:
        bills = response.json().get("bills", [])
        current_hash = hashlib.md5(json.dumps(bills, sort_keys=True).encode()).hexdigest()
        cached_hash = cache.get('bills_hash')
        
        if current_hash != cached_hash:
            print("Cache updated with new bills data")
            cache.set('bills_data', bills, timeout=None)
            cache.set('bills_hash', current_hash, timeout=None)
            return "Cache updated"
    return "No changes"


def home(request):
    bills = cache.get('bills_data', [])
    return render(request, "core/home.html", {"bills": bills})
