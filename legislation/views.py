# legislation/views.py
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
import requests
import os
from dotenv import load_dotenv
from congress.models import Congress, Member
from legislation.models import Bills
from django.views.decorators.cache import cache_page
from django.core.cache import cache

import math

load_dotenv()
API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"
CACHE_TIMEOUT = 60 * 15
CONGRESS_REAL_COUNTS = {}


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

    endpoint_type = None
    template_name = None
    partial_template_name = None
    context_key = None

    def get(self, request):
        congress_id = request.GET.get("congress")
        page = request.GET.get("page", 1)

        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1

        limit = 12
        offset = (page - 1) * limit
        pagination_cache_key = f"{congress_id}_{self.endpoint_type}"
        api_cache_key = f"api_data_{congress_id}_{self.endpoint_type}_{page}_{limit}"

        cached_api_data = cache.get(api_cache_key)

        if cached_api_data is not None:
            response_data = cached_api_data
            response_status = 200
        else:
            url = f"{BASE_URL}/{self.endpoint_type}/{congress_id}?api_key={API_KEY}&limit={limit}&offset={offset}"
            response = requests.get(url)
            response_status = response.status_code

            if response_status == 200:
                response_data = response.json()
                cache.set(api_cache_key, response_data, CACHE_TIMEOUT)
            else:
                response_data = {}

        if response_status == 200:
            api_key = "bills" if self.endpoint_type == "law" else self.context_key
            data = response_data.get(api_key, [])

            pagination = response_data.get("pagination", {})
            api_total_count = pagination.get("count", 0)

            if pagination_cache_key in CONGRESS_REAL_COUNTS:
                real_total_count = CONGRESS_REAL_COUNTS[pagination_cache_key]
                total_pages = (
                    math.ceil(real_total_count / limit) if real_total_count > 0 else 1
                )
                total_count = real_total_count
            else:
                total_count = api_total_count
                total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

                if len(data) == 0 and page > 1:
                    real_total_count = (page - 1) * limit
                    CONGRESS_REAL_COUNTS[pagination_cache_key] = real_total_count
                    total_count = real_total_count
                    total_pages = page - 1

            page_obj = SimplePagination(page, total_pages, total_count)
            page_range = self.get_page_range(page, total_pages)

        else:
            data = []
            page_obj = SimplePagination(1, 1, 0)
            page_range = [1]

        context = {
            self.context_key: data,
            "url": f"{BASE_URL}/{self.endpoint_type}/{congress_id}?api_key={API_KEY}&limit={limit}&offset={offset}",
            "page_obj": page_obj,
            "page_range": page_range,
            "congress_id": congress_id,
            "request": request,
        }

        if request.headers.get("HX-Request"):
            return render(request, self.partial_template_name, context)
        return render(request, self.template_name, context)

    def get_page_range(self, current_page, total_pages, on_each_side=2):
        """Create a page range similar to Django's get_elided_page_range"""
        if total_pages <= 7:
            return list(range(1, total_pages + 1))

        start = max(1, current_page - on_each_side)
        end = min(total_pages, current_page + on_each_side)

        page_range = list(range(start, end + 1))

        if start > 1:
            if start > 2:
                page_range = [1, "…"] + page_range
            else:
                page_range = [1] + page_range

        if end < total_pages:
            if end < total_pages - 1:
                page_range = page_range + ["…", total_pages]
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


@require_http_methods(["GET"])
def bill_details_htmx(request):
    """HTMX endpoint to fetch and render detailed bill information"""
    api_url = request.GET.get("url")
    
    if api_url:
        separator = "&" if "?" in api_url else "?"
        api_url_with_key = f"{api_url}{separator}api_key={API_KEY}"
    else:
        api_url_with_key = None
    
    try:
        response = requests.get(api_url_with_key, timeout=10)
        response.raise_for_status()
        bill_data = response.json().get("bill", {})
        
        try:
            db_bill = Bills.objects.get(
                originChamber=bill_data.get("type").lower(),
                number=bill_data.get("number"),
                congress__congress_number=bill_data.get("congress"),
            )
        except Bills.DoesNotExist:
            db_bill = None
        
        if "sponsors" in bill_data:
            for sponsor in bill_data["sponsors"]:
                try:
                    member = Member.objects.get(bioguide_id=sponsor["bioguideId"])
                    sponsor["member_pk"] = member.pk
                    sponsor["has_detail_page"] = True
                except Member.DoesNotExist:
                    sponsor["member_pk"] = None
                    sponsor["has_detail_page"] = False
        
        return render(
            request, "legislation/partials/bill_details_modal.html", 
            {"bill": bill_data, "db_bill": db_bill}
        )
        
    except requests.RequestException as e:
        return HttpResponse(
            f"""
            <div class="alert alert-error">
                <span>Failed to fetch bill details: {str(e)}</span>
            </div>
            """
        )

im_just_a_bill = BillView.as_view()
laws = LawView.as_view()
