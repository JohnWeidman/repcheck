from google import genai
from google.genai import types
import os
import json  # Add this import
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from legislation.models import Bills
import httpx

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # bill = fetch_bill()
        Process_with_Gemini()
        print("Booya")

def fetch_bill():
    #This is where I will fetch the pdf for the bill?
    pass

def Process_with_Gemini():
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    doc_url = "https://www.congress.gov/119/bills/hr3076/BILLS-119hr3076ih.pdf" #will be programatic later
    doc_data = httpx.get(doc_url).content
    
    prompt = "Summarize this bill, provide key changes and provisions. Also provide 3 tags"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        
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
            'summary': summary,
            'tags': tags,  
        }
    )
    
    print(f"Bill {'created' if created else 'updated'}: {bill_obj}")
    return bill_obj



