from django.shortcuts import render
from django.core.cache import cache
from google import genai
from google.genai import types
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from dotenv import load_dotenv
import requests
import os
import hashlib
import json
from .models import DailyCongressRecord
from congress.models import Member, Congress, Membership
from legislation.models import Bills
from django.shortcuts import render
from django.views.decorators.cache import cache_page
import requests
import os
from dotenv import load_dotenv


load_dotenv()
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Create your views here.

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"
CACHE_TIMEOUT = 60 * 15  # 10 minutes


def home(request):
    # Get bills from cache (populated by background task)
    bills = cache.get("bills_data", [])

    # Get daily congress record
    today = DailyCongressRecord.objects.order_by("-issue_date").first()

    if today:
        summary = today.summary
        pdf_url = today.pdf_url
    else:
        summary = "No summary available for today."
        pdf_url = None

    return render(
        request, "core/home.html", {"bills": bills, "summary": summary, "url": pdf_url}
    )


def search_page(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        search_query = SearchQuery(query)

        # Search members directly
        members = (
            Member.objects.annotate(
                search=SearchVector("name", "state"),
                rank=SearchRank(SearchVector("name", "state"), search_query),
            )
            .filter(search=search_query)
            .order_by("-rank")
        )

        # Add to results list with type info
        for member in members:
            results.append(
                {
                    "object": member,
                    "kind": "member",
                    "title": member.full_name(),
                    "pk": member.pk,
                    "snippet": f"{member.full_name()} ({member.state})",
                    "state": member.state,
                    "party": (
                        Membership.objects.filter(member=member).last().party
                        if Membership.objects.filter(member=member).exists()
                        else "N/A"
                    ),
                    "district": (
                        Membership.objects.filter(member=member).last().district
                        if Membership.objects.filter(member=member).exists()
                        else "N/A"
                    ),
                    "image_url": member.image_url,
                    "full_name": member.full_name(),
                }
            )

        # Search congress sessions
        congresses = (
            Congress.objects.annotate(
                search=SearchVector("congress_number"),
                rank=SearchRank(SearchVector("congress_number"), search_query),
            )
            .filter(search=search_query)
            .order_by("-rank")[:10]
        )

        for congress in congresses:
            results.append(
                {
                    "object": congress,
                    "kind": "congress",
                    "title": f"Congress {congress.congress_number}",
                    "snippet": f"Congress {congress.congress_number} ({congress.start_date.year})",
                }
            )
        # Search bills
        bills = (
            Bills.objects.annotate(
                search=SearchVector(
                    "title", "gemini_summary", "type", "number", "tags"
                ),
                rank=SearchRank(
                    SearchVector("title", "gemini_summary", "type", "number", "tags"),
                    search_query,
                ),
            )
            .filter(search=search_query)
            .order_by("-rank")
        )

        for bill in bills:
            results.append(
                {
                    "object": bill,
                    "kind": "bill",
                    "title": bill.title,
                    "snippet": f"{bill.number}: {bill.gemini_summary}...",
                    "gemini_summary": bill.gemini_summary,
                    "number": bill.number,
                    "congress": bill.congress_id,
                    "type": bill.type,
                    "url": bill.url,
                }
            )

    return render(request, "core/search.html", {"query": query, "results": results})
