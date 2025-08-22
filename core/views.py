from django.shortcuts import render
from django.core.cache import cache
from google import genai
from google.genai import types
import httpx
from dotenv import load_dotenv
from celery import shared_task
import requests
import os
import hashlib
import json
from .models import DailyCongressRecord

load_dotenv()
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Create your views here.

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"
CACHE_TIMEOUT = 60 * 15  # 10 minutes


@shared_task
def update_bills_cache(force_update=False):
    url = f"{BASE_URL}/bill?api_key={API_KEY}&limit=12"
    response = requests.get(url)
    
    if response.status_code == 200:
        bills = response.json().get("bills", [])
        current_hash = hashlib.md5(
            json.dumps(bills, sort_keys=True).encode()
        ).hexdigest()
        
        cached_hash = cache.get("bills_hash")
        
        if force_update or current_hash != cached_hash:
            print("Cache updated with new bills data")
            cache.set("bills_data", bills, timeout=None)
            cache.set("bills_hash", current_hash, timeout=None)
            return "Cache updated"
        return "No changes"
    
    return f"API Error: {response.status_code}"


def home(request):
    today = DailyCongressRecord.objects.order_by('-issue_date').first()
    summary = today.summary if today else "No summary available for today."
    url = today.pdf_url
    bills = cache.get("bills_data", [])
    return render(request, "core/home.html", {"bills": bills, "summary": summary, "url": url})
