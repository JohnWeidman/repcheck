from google import genai
from google.genai import types
import os
import requests
import json
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from legislation.models import Bills
from congress.models import Congress
import httpx

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        bills = fetch_bills()
        print(f"Fetched {len(bills)} bills from Congress API.")
        Process_with_Gemini(bills)
        print("Booya")


def fetch_bills():
    bills = []
    offset = 0
    limit = 12
    # This is where I will fetch the pdf for the bill?
    # url format: /bill/{congress}/{billType}/{billNumber}/text
    # textVersions > most recent entry is 0 >  type=PDF
    while offset <= 24:
        congress = Congress.get_current_congress_number()
        url = f"{BASE_URL}/bill/{congress}/?api_key={API_KEY}&offset={offset}&limit={limit}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            break
        data = response.json()
        pagination_info = data.get("pagination", {})
        next_page = pagination_info.get("next")

        if "bills" in data:
            bills.extend(data["bills"])
            print(f"Fetched {len(bills)} bills")
        else:
            print("No bills found in the response.")
            break
        if next_page:
            offset += limit
        else:
            print("Finished fetching bills.")
            break
    return bills


def Process_with_Gemini(bills):
    client = genai.Client(api_key=GEMINI_API_KEY)
    if not bills:
        print("No bills to process.")
        return
    for bill in bills:
        congress_instance = Congress.get_current_congress_object()
        title = bill.get("title")
        origin_chamber = bill.get("originChamber")
        bill_number = bill.get("number")
        bill_type = bill.get("type").lower()
        congress = bill.get("congress")
        latest_action_date = bill.get("latestAction").get("actionDate") if bill.get("latestAction") else None
        
        text_versions_url = f"{BASE_URL}/bill/{congress}/{bill_type}/{bill_number}/text?api_key={API_KEY}&format=json"
        print(text_versions_url)
        text_versions_response = requests.get(text_versions_url)
        print(text_versions_response)
    
        if text_versions_response.status_code != 200:
            print(f"Error fetching text versions: {text_versions_response.status_code}")
            continue
      
        text_versions_data = text_versions_response.json().get("textVersions", [])
        print(text_versions_data)
        if not text_versions_data:
            print(f"No text versions found for bill {bill_number}.")
            continue
        
        most_recent_version = text_versions_data[0] 
        print(f"Most recent version for bill {bill_number}: {most_recent_version}")
        pdf_version = next((f for f in most_recent_version.get("formats", []) if f.get("type") == "PDF"), None)
        
        if not pdf_version:
            print(f"No PDF version found for bill {bill_number}.")
            continue
        
        full_text_url = pdf_version.get("url")
        
        
            
        if not (bill_number and bill_type and congress):
            print("Skipping bill due to missing information.")
            continue
        
        print(f"Processing Bill: {bill_number} of Congress {congress}")
        
        doc_data = httpx.get(full_text_url).content

        prompt = "Summarize this bill in high school level language, provide key changes and provisions. Also provide 3 tags under 25 characters each"
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=[
                types.Part.from_bytes(data=doc_data, mime_type="application/pdf"),
                prompt,
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "A short summary of the legislation.",
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": "A tag related to the legislation.",
                            },
                        },
                    },
                },
            },
        )

        data = json.loads(response.text)
        summary = data.get("summary")
        tags = data.get("tags", [])

        bill_obj, created = Bills.objects.update_or_create(
            bill_number=bill_number,
            type=bill_type,
            defaults={
                "gemini_summary": summary,
                "tags": tags,
                "bill_number": bill_number,
                "type": bill_type,
                "congress": congress_instance,
                "latest_action_date": latest_action_date,
                "title": title,
                "origin_chamber": origin_chamber,
                "full_text_url": full_text_url,
            }
        )

