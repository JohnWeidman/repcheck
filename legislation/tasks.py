from celery import shared_task
from celery.exceptions import Retry
from google import genai
from google.genai import types
import os
import requests
import json
import httpx
import logging
import time
import urllib.parse
from datetime import datetime, timedelta
from .models import Bills
from congress.models import Congress

logger = logging.getLogger(__name__)
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_RPM = 15
GEMINI_RPD = 1000
GEMINI_TPM = 1000000


@shared_task(name="legislation.tasks.fetch_and_process_bills_task")
def fetch_and_process_bills_task():
    """
    Scheduled task to fetch bills from Congress API and process with Gemini
    """
    try:
        logger.info("Starting scheduled bill fetch and processing task")
        bills = fetch_bills_from_api()
        logger.info(f"Fetched {len(bills)} bills from Congress API")

        if bills:
            process_bills_with_gemini.delay(bills)
            return f"Queued {len(bills)} bills for processing"
        else:
            logger.warning("No bills data retrieved from API")
            return "No bills data retrieved"

    except Exception as e:
        logger.error(f"Error in fetch_and_process_bills_task: {str(e)}")
        raise


def fetch_bills_from_api():
    """Fetch bills modified in the last 4 hours from Congress API"""
    API_KEY = os.getenv("CONGRESS_API_KEY")
    BASE_URL = "https://api.congress.gov/v3"

    bills = []
    offset = 0
    limit = 250

    now = datetime.now()
    then = now - timedelta(minutes=15)

    to_datetime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    from_datetime = then.strftime("%Y-%m-%dT%H:%M:%SZ")

    from_datetime_encoded = urllib.parse.quote(from_datetime)
    to_datetime_encoded = urllib.parse.quote(to_datetime)

    while True:
        url = f"{BASE_URL}/bill/119?format=json&fromDateTime={from_datetime_encoded}&toDateTime={to_datetime_encoded}&api_key={API_KEY}&offset={offset}&limit={limit}"

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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_bills_with_gemini(self, bills):
    """Process bills with Gemini with proper rate limiting"""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=GEMINI_API_KEY)

    if not bills:
        logger.warning("No bills to process")
        return 0

    processed_count = 0
    last_request_time = time.time()

    for bill in bills:
        try:
            # Rate limiting: wait at least 4 seconds between requests (15/min max)
            current_time = time.time()
            time_since_last = current_time - last_request_time
            if time_since_last < 4:
                sleep_time = 4 - time_since_last
                logger.info(f"Rate limiting: sleeping {sleep_time:.1f} seconds")
                time.sleep(sleep_time)

            result = process_single_bill_with_gemini(bill, client)
            last_request_time = time.time()

            if result:
                processed_count += 1

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning(f"Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                # Retry this bill
                try:
                    result = process_single_bill_with_gemini(bill, client)
                    if result:
                        processed_count += 1
                except Exception as retry_e:
                    logger.error(f"Retry failed for bill: {retry_e}")
            else:
                logger.error(f"Error processing bill: {e}")
            continue

    return processed_count


def process_single_bill_with_gemini(bill, client=None):
    """Process a single bill with Gemini"""
    # Initialize variables at the top to avoid reference errors
    bill_number = "unknown"
    congress_number = "unknown"

    try:
        if not client:
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            client = genai.Client(api_key=GEMINI_API_KEY)

        API_KEY = os.getenv("CONGRESS_API_KEY")
        BASE_URL = "https://api.congress.gov/v3"

        # Extract bill information
        congress_number = bill.get("congress")
        title = bill.get("title")
        origin_chamber = bill.get("originChamber")
        bill_number = bill.get("number")
        bill_type = bill.get("type").lower()
        latest_action_date = (
            bill.get("latestAction").get("actionDate")
            if bill.get("latestAction")
            else None
        )

        # Get or create the Congress instance
        try:
            congress_instance = Congress.objects.get(congress_number=congress_number)
        except Congress.DoesNotExist:
            congress_instance = Congress.objects.create(congress_number=congress_number)
            logger.info(f"Created new Congress instance for congress {congress_number}")

        # Prepare default fields - USE CONGRESS ID, NOT THE INSTANCE
        defaults = {
            "bill_number": bill_number,
            "type": bill_type,
            "congress_id": congress_instance.id,  # Use the ID, not the instance!
            "latest_action_date": latest_action_date,
            "title": title,
            "origin_chamber": origin_chamber,
        }

        # Check for existing bill
        existing_bill = None
        try:
            existing_bill = Bills.objects.get(
                bill_number=bill_number,
                type=bill_type,
                congress_id=congress_instance.id,  # Use the ID, not the instance!
            )
        except Bills.DoesNotExist:
            logger.info(f"New bill {bill_number} - will process with Gemini")

        # Use congress_number for API calls
        text_versions_url = f"{BASE_URL}/bill/{congress_number}/{bill_type}/{bill_number}/text?api_key={API_KEY}&format=json"
        text_versions_response = requests.get(text_versions_url)

        process_with_gemini = False

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
                    current_text_url = pdf_version.get("url")
                    defaults["full_text_url"] = current_text_url

                    if existing_bill is None:
                        process_with_gemini = True
                        logger.info(f"Processing new bill {bill_number} with Gemini")
                    elif existing_bill.full_text_url != current_text_url:
                        process_with_gemini = True
                        logger.info(
                            f"Bill {bill_number} has new text version, reprocessing with Gemini"
                        )
                    else:
                        # Preserve existing Gemini data if no text changes
                        if existing_bill.gemini_summary:
                            defaults["gemini_summary"] = existing_bill.gemini_summary
                        if existing_bill.tags:
                            defaults["tags"] = existing_bill.tags
                        logger.info(
                            f"Bill {bill_number} already processed with same text version, skipping Gemini processing"
                        )

                    if process_with_gemini:
                        try:
                            logger.info(
                                f"Processing Bill: {bill_number} of Congress {congress_number}"
                            )

                            doc_data = httpx.get(current_text_url).content
                            prompt = "Summarize this bill in high school level language, provide key changes and provisions. Also provide 3 tags under 25 characters each"

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

        # Always save the bill to keep metadata updated
        bill_obj, created = Bills.objects.update_or_create(
            bill_number=bill_number,
            type=bill_type,
            congress_id=congress_instance.id,  # Use the ID, not the instance!
            defaults=defaults,
        )

        action = "created" if created else "updated"
        gemini_status = "with Gemini" if process_with_gemini else "metadata only"
        logger.info(f"Successfully {action} bill {bill_number} ({gemini_status})")
        return True

    except Exception as e:
        logger.error(
            f"Unexpected error processing bill {bill_number} from congress {congress_number}: {e}"
        )
        return False
