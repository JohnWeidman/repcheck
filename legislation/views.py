# legislation/views.py
from django.shortcuts import render, get_object_or_404
from django.views import View
import requests
import os
from dotenv import load_dotenv
from congress.models import Congress

load_dotenv()
API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"


class LegislationView(View):
    """Generic view for legislation (bills or laws)"""
    endpoint_type = None  # Override in subclasses
    template_name = None
    partial_template_name = None
    context_key = None
    
    def get(self, request):
        congress_id = request.GET.get("congress")
        
        url = f"{BASE_URL}/{self.endpoint_type}/{congress_id}?api_key={API_KEY}&limit=12"
        
        response = requests.get(url)
        if response.status_code == 200:
            # For laws endpoint, API still returns "bills" key
            api_key = "bills" if self.endpoint_type == "law" else self.context_key
            data = response.json().get(api_key, [])
        else:
            data = []
        
        context = {
            self.context_key: data,
            "url": url,
        }
        
        # Return partial template for HTMX requests, full template otherwise
        if request.headers.get("HX-Request"):
            return render(request, self.partial_template_name, context)
        return render(request, self.template_name, context)


class BillView(LegislationView):
    endpoint_type = "bill"
    template_name = "legislation/bills.html"
    partial_template_name = "legislation/partials/bills_partial.html"
    context_key = "bills"


class LawView(LegislationView):
    endpoint_type = "law"
    template_name = "legislation/laws.html"
    partial_template_name = "legislation/partials/laws_partial.html"
    context_key = "laws"


def legislation_landing_page(request):
    congresses = Congress.objects.all()
    context = {
        "congresses": congresses,
    }
    return render(request, "legislation/legislation.html", context)


# Create view instances
im_just_a_bill = BillView.as_view()
laws = LawView.as_view()