from celery import shared_task
import requests
import httpx
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .models import DailyCongressRecord


load_dotenv()
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3"



@shared_task
def fetch_daily_congress_record():
        url = (f"{BASE_URL}/daily-congressional-record/?limit=1&api_key={API_KEY}&format=json")
        response = requests.get(url)
        if response.status_code == 200:
            print("Successfully fetched most recent congressional record date")
            data = response.json()
            if data:
                date = data["dailyCongressionalRecord"][0]["issueDate"]
                print(f"Most recent congressional record date: {date}")
                cleaned_date = date.split("T")[0]
                year, month, day = cleaned_date.split("-")
                print(f"Most recent congressional record date: {year}-{month}-{day}")
                url = f"{BASE_URL}/congressional-record/?y={year}&m={month}&d={day}&api_key={API_KEY}&format=json"
                second_response = requests.get(url)
                if second_response.status_code == 200:
                    print("testes")
                    data = second_response.json()
                    if data:
                        record_url = data["Results"]["Issues"][0]["Links"]["Digest"]["PDF"][
                            0
                        ]["Url"]
                        try:
                            doc_data = httpx.get(record_url).content
                            prompt = "Summarize the daily congressional digest in plain (high school level) language. Do not use technical jargon. The summary should be concise and easy to understand."

                            client = genai.Client(api_key=GEMINI_API_KEY)
                            print("Generating summary using Gemini API...")
                            response = client.models.generate_content(
                                model=GEMINI_MODEL,
                                contents=[
                                    types.Part.from_bytes(
                                        data=doc_data, mime_type="application/pdf"
                                    ),
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
                                            "date": {
                                                "type": "string",
                                                "description": "The date of the congressional record.",
                                            },
                                        },
                                    },
                                },
                            )
                            data = json.loads(response.text)
                            summary = data.get("summary", "No summary available")
                            print(f"Summary: {summary}")
                            url = record_url
                        except Exception as e:
                            print(f"Error generating summary: {e}")
                            url = "fubar"
                    else:
                        url = "fubar"
                else:
                    print("Failed to fetch congressional record details")
        else:
            print(
                " Failed to fetch most recent congressional record date",
                response.status_code,
            )