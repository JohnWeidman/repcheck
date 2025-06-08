from django.shortcuts import render, get_object_or_404
from congress.models import Congress

import requests
import os

BASE_URL = "https://api.congress.gov/v3/"
API_KEY = os.getenv("CONGRESS_API_KEY")


def legislation_landing_page(request):
    context = {
        "congresses": Congress.objects.all(),
    }
    return render(request, "legislation/legislation.html", context)


def im_just_a_bill(request):
    congress_id = request.GET.get("congress")
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None

    url = f"{BASE_URL}bill/{congress.congress_number}?limit=10&api_key={API_KEY}"
    context = {
        "bills": [],
        "bill_count": 0,
    }
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        bills = data.get("bills", [])
        for bill in bills:
            bill["title"] = bill.get("title", "No Title Available")
            bill["number"] = bill.get("number", "No Number Available")

        context = {
            "bills": bills,
            "bill_count": len(bills),
        }
    if request.headers.get("HX-Request"):
        return render(request, "legislation/partials/bills_partial.html", context)
    return render(request, "legislation/bills.html", context)


def laws(request):
    congress_id = request.GET.get("congress")
    congress = get_object_or_404(Congress, id=congress_id) if congress_id else None
    url = f"{BASE_URL}bill/{congress.congress_number}?limit=10&api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        laws = data.get("bills", [])
        for law in laws:
            law["title"] = law.get("title", "No Title Available")
            law["number"] = law.get("number", "No Number Available")

        context = {
            "laws": laws,
            "law_count": len(laws),
        }
    if request.headers.get("HX-Request"):
        return render(request, "legislation/partials/laws_partial.html", context)
    return render(request, "legislation/laws.html", context)


def bill_detail(request, bill_id, bill_type, congress):
    url = f"{BASE_URL}bill/{congress}/{bill_type}/{bill_id}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        bill = data.get("bill")
        context = {
            "bill": bill,
        }
    else:
        context = {
            "error": "Bill not found or API error.",
        }

    return render(request, "bill_detail.html", context)


def law_detail(request, law_id):
    url = f"{BASE_URL}law/{law_id}?api_key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        law = response.json()
        context = {
            "law": law,
        }
    else:
        context = {
            "error": "Law not found or API error.",
        }

    if request.headers.get("HX-Request"):
        return render(request, "legislation/partials/law_detail_partial.html", context)
    return render(request, "legislation/law_detail.html", context)
