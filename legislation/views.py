from django.shortcuts import render
import requests
import os

API_KEY = os.getenv('CONGRESS_API_KEY')

def legislation_landing_page(request):
    return render(request, 'legislation/legislation.html')

def im_just_a_bill(request):
    response = requests.get("https://api.congress.gov/v3/bill/119?limit=10&api_key=" + API_KEY)
    if response.status_code == 200:
        data = response.json()
        bills = data.get('bills', [])
        for bill in bills:
            bill['title'] = bill.get('title', 'No Title Available')
            bill['number'] = bill.get('number', 'No Number Available')
        
        context = {
            'bills': bills,
            'bill_count': len(bills),
        }
    if request.headers.get("HX-Request"):
        return render(request, "legislation/partials/bills_partial.html", context)
    return render(request, "legislation/bills.html", context)

def laws(request):
    if request.headers.get("HX-Request"):
        return render(request, "legislation/partials/laws_partial.html")
    return render(request, "legislation/laws.html")