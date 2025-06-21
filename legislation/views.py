# legislation/views.py
from django.shortcuts import render, get_object_or_404
from django.views import View
import requests
import os
from dotenv import load_dotenv
from congress.models import Congress
import math

load_dotenv()
API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"

class SimplePagination:
    def __init__(self, current_page, total_pages, total_count):
        self.number = current_page
        self.num_pages = total_pages
        self.count = total_count
        
    def has_previous(self):
        return self.number > 1
        
    def has_next(self):
        return self.number < self.num_pages
        
    def previous_page_number(self):
        return self.number - 1 if self.has_previous() else None
        
    def next_page_number(self):
        return self.number + 1 if self.has_next() else None

class LegislationView(View):
    """Generic view for legislation (bills or laws)"""
    endpoint_type = None # Override in subclasses
    template_name = None
    partial_template_name = None
    context_key = None
    
    def get(self, request):
        congress_id = request.GET.get("congress")
        page = request.GET.get("page", 1)
        
        # Convert page to offset for the API
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
            
        limit = 12  # Items per page
        offset = (page - 1) * limit
        
        url = f"{BASE_URL}/{self.endpoint_type}/{congress_id}?api_key={API_KEY}&limit={limit}&offset={offset}"
        response = requests.get(url)
        
        if response.status_code == 200:
            response_data = response.json()
            # For laws endpoint, API still returns "bills" key
            api_key = "bills" if self.endpoint_type == "law" else self.context_key
            data = response_data.get(api_key, [])
            
            # Get pagination info from API response
            pagination = response_data.get("pagination", {})
            total_count = pagination.get("count", 0)
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
            
            page_obj = SimplePagination(page, total_pages, total_count)
            
            # Create page range for pagination component
            page_range = self.get_page_range(page, total_pages)
            
        else:
            data = []
            page_obj = SimplePagination(1, 1, 0)
            page_range = [1]
        
        context = {
            self.context_key: data,
            "url": url,
            "page_obj": page_obj,
            "page_range": page_range,
            "congress_id": congress_id,
            "request": request,
        }
        
        # Return partial template for HTMX requests, full template otherwise
        if request.headers.get("HX-Request"):
            return render(request, self.partial_template_name, context)
        return render(request, self.template_name, context)
    
    def get_page_range(self, current_page, total_pages, on_each_side=2):
        """Create a page range similar to Django's get_elided_page_range"""
        if total_pages <= 7:  # Show all pages if 7 or fewer
            return list(range(1, total_pages + 1))
        
        # Show current page with context
        start = max(1, current_page - on_each_side)
        end = min(total_pages, current_page + on_each_side)
        
        page_range = list(range(start, end + 1))
        
        # Add ellipsis and boundary pages if needed
        if start > 1:
            if start > 2:
                page_range = [1, '…'] + page_range
            else:
                page_range = [1] + page_range
                
        if end < total_pages:
            if end < total_pages - 1:
                page_range = page_range + ['…', total_pages]
            else:
                page_range = page_range + [total_pages]
        
        return page_range

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