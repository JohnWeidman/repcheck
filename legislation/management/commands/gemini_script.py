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
        # bill = fetch_bills()
        Process_with_Gemini()
        print("Booya")

def fetch_bills():
    bills = []
    offset = 0
    limit = 12
    #This is where I will fetch the pdf for the bill?
    # url format: /bill/{congress}/{billType}/{billNumber}/text
        #textVersions > most recent entry is 0 >  type=PDF
    while offset <= 24:
        congress = Congress.get_current_congress()
        url = f"{BASE_URL}/bill/{congress}/?api_key={API_KEY}&offset={offset}&limit={limit}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            break
        data = response.json()
        
        if "bills" in data:
            bills.extend(data["bills"])
            print(f"Fetched {len(bills)} bills")
          
    
    
    return bills

def Process_with_Gemini():
    client = genai.Client(api_key=GEMINI_API_KEY)
    doc_url = "https://www.congress.gov/119/bills/hr3076/BILLS-119hr3076ih.pdf" #will be programatic later
    doc_data = httpx.get(doc_url).content
    
    prompt = "Summarize this bill, provide key changes and provisions. Also provide 3 tags under 25 characters each"
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        
        contents=[
            types.Part.from_bytes(
                data=doc_data,
                mime_type='application/pdf'
            ),
            prompt
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
        defaults={
            'gemini_summary': summary,
            'tags': tags,  
        }
    )
    
    print(f"Bill {'created' if created else 'updated'}: {bill_obj}")
    return bill_obj



