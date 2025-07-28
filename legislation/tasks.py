from celery import shared_task
from google import genai
from google.genai import types
import os
import requests
import json
import httpx
import logging
from django.conf import settings
from .models import Bills
from congress.models import Congress

logger = logging.getLogger(__name__)
GEMINI_MODEL = "gemini-2.5-flash-lite"  # Use the appropriate Gemini model
GEMINI_RPD = 200 # Requests Per Day limit for Gemini API
GEMINI_TPM = 1000000 # Tokens per minute limit for Gemini API


@shared_task(name='legislation.tasks.fetch_and_process_bills_task')
def fetch_and_process_bills_task():
    """
    Scheduled task to fetch bills from Congress API and process with Gemini
    """
    try:
        logger.info("Starting scheduled bill fetch and processing task")

        bills = fetch_bills_from_api()
        logger.info(f"Fetched {len(bills)} bills from Congress API")

        if bills:
            processed_count = process_bills_with_gemini(bills)
            logger.info(f"Successfully processed {processed_count} bills with Gemini")
            return f"Processed {processed_count} bills successfully"
        else:
            logger.warning("No bills data retrieved from API")
            return "No bills data retrieved"

    except Exception as e:
        logger.error(f"Error in fetch_and_process_bills_task: {str(e)}")
        raise


@shared_task
def process_single_bill_task(bill_data):
    """
    Task to process a single bill with Gemini (for parallel processing)
    """
    try:
        return process_single_bill_with_gemini(bill_data)
    except Exception as e:
        logger.error(f"Error processing single bill: {str(e)}")
        raise


def fetch_bills_from_api():
    """Fetch bills modified in the last 15 minutes from Congress API"""
    API_KEY = os.getenv("CONGRESS_API_KEY")
    BASE_URL = "https://api.congress.gov/v3"

    bills = []
    offset = 0
    limit = 250

    from datetime import datetime, timedelta
    import urllib.parse

    now = datetime.now()
    fifteen_minutes_ago = now - timedelta(minutes=15)

    to_datetime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    from_datetime = fifteen_minutes_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

    from_datetime_encoded = urllib.parse.quote(from_datetime)
    to_datetime_encoded = urllib.parse.quote(to_datetime)

    while True:
        url = f"{BASE_URL}/bill?format=json&fromDateTime={from_datetime_encoded}&toDateTime={to_datetime_encoded}&api_key={API_KEY}&offset={offset}&limit={limit}"

        logger.info(f"Fetching bills from {from_datetime} to {to_datetime}")
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Error fetching data: {response.status_code}")
            break

        data = response.json()
        pagination_info = data.get("pagination", {})
        next_page = pagination_info.get("next")

        if "bills" in data and data["bills"]:
            bills.extend(data["bills"])
            logger.info(f"Fetched {len(data['bills'])} bills (total: {len(bills)})")
        else:
            logger.info("No bills found in this time range")
            break

        if next_page:
            offset += limit
        else:
            logger.info("Finished fetching bills")
            break

    return bills


def process_bills_with_gemini(bills):
    """Process bills with Gemini - extracted from your management command"""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=GEMINI_API_KEY)

    if not bills:
        logger.warning("No bills to process")
        return 0

    processed_count = 0

    for bill in bills:
        try:
            result = process_single_bill_with_gemini(bill, client)
            if result:
                processed_count += 1
        except Exception as e:
            logger.error(f"Error processing bill: {e}")
            continue

    return processed_count


def process_single_bill_with_gemini(bill, client=None):
    """Process a single bill with Gemini"""
    if not client:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=GEMINI_API_KEY)

    API_KEY = os.getenv("CONGRESS_API_KEY")
    BASE_URL = "https://api.congress.gov/v3"

    try:
        congress_instance = Congress.get_current_congress_object()
        title = bill.get("title")
        origin_chamber = bill.get("originChamber")
        bill_number = bill.get("number")
        bill_type = bill.get("type").lower()
        congress = bill.get("congress")
        latest_action_date = (
            bill.get("latestAction").get("actionDate")
            if bill.get("latestAction")
            else None
        )

        # Prepare default fields
        defaults = {
            "bill_number": bill_number,
            "type": bill_type,
            "congress": congress_instance,
            "latest_action_date": latest_action_date,
            "title": title,
            "origin_chamber": origin_chamber,
        }

        # Try to get Gemini data
        text_versions_url = f"{BASE_URL}/bill/{congress}/{bill_type}/{bill_number}/text?api_key={API_KEY}&format=json"
        text_versions_response = requests.get(text_versions_url)

        if text_versions_response.status_code == 200:
            text_versions_data = text_versions_response.json().get("textVersions", [])

            if text_versions_data:
                most_recent_version = text_versions_data[0]
                pdf_version = next(
                    (
                        f
                        for f in most_recent_version.get("formats", [])
                        if f.get("type") == "PDF"
                    ),
                    None,
                )

                if pdf_version:
                    full_text_url = pdf_version.get("url")
                    defaults["full_text_url"] = full_text_url

                    try:
                        logger.info(
                            f"Processing Bill: {bill_number} of Congress {congress}"
                        )

                        doc_data = httpx.get(full_text_url).content
                        prompt = "Summarize this bill in high school level language, provide key changes and provisions. Also provide 3 tags under 25 characters each"

                        response = client.models.generate_content(
                            model= GEMINI_MODEL,
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

                        # Process Gemini response
                        data = json.loads(response.text)
                        defaults["gemini_summary"] = data.get("summary")
                        defaults["tags"] = data.get("tags", [])

                    except Exception as e:
                        logger.error(
                            f"Error with Gemini processing for bill {bill_number}: {e}"
                        )

        # Save the bill with whatever data we have
        bill_obj, created = Bills.objects.update_or_create(
            bill_number=bill_number, type=bill_type, defaults=defaults
        )

        logger.info(f"Successfully saved bill {bill_number} (created: {created})")
        return True

    except Exception as e:
        logger.error(f"Unexpected error processing bill {bill_number}: {e}")
        return False
