from google import genai
import os
import json  # Add this import
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from legislation.models import Bills

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Process_with_Gemini()
        print("Booya")

def fetch_bill():
    pass

def Process_with_Gemini():
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="""Generate a short summary,
 including key provisions and major changes, and 3-5 tags
 for the following legislation:
 https://www.congress.gov/119/bills/hr3599/BILLS-119hr3599ih.pdf""",
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