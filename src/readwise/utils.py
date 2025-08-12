import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables early
load_dotenv()

# Configuration
READWISE_TOKEN = os.getenv("READWISE_TOKEN")
API_URL = "https://readwise.io/api/v3/list/"

def fetch_all_documents(category=None, location=None):
    """Fetch all documents from the Readwise Reader API, handling pagination."""
    if not READWISE_TOKEN:
        raise ValueError("Missing READWISE_TOKEN in environment variables. Ensure it's set in your .env file.")

    all_docs = []
    next_cursor = None

    print(f"Starting fetch... Category: {category}, Location: {location}")

    while True:
        params = {}
        if category:
            params["category"] = category
        if location:
            params["location"] = location
        if next_cursor:
            params["pageCursor"] = next_cursor

        print(f"Fetching page with params: {params}") # Debug print
        try:
            response = requests.get(
                API_URL,
                headers={"Authorization": f"Token {READWISE_TOKEN}"},
                params=params,
                timeout=30 # Add a timeout
            )
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
            # Decide how to handle: retry, raise, return partial etc.
            # For now, we'll raise an exception to stop the process
            raise Exception(f"API Request Failed: {e}") from e

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError as e:
             print(f"Error decoding JSON response: {e}")
             print(f"Response status code: {response.status_code}")
             print(f"Response text: {response.text[:500]}...") # Print start of response text
             raise Exception("Failed to decode API response JSON.") from e

        results = data.get("results", [])
        all_docs.extend(results)
        next_cursor = data.get("nextPageCursor")

        print(f"Fetched {len(results)} documents. Total: {len(all_docs)}. Next cursor: {'Yes' if next_cursor else 'No'}")

        if not next_cursor:
            break

    print(f"Finished fetching. Total documents: {len(all_docs)}")
    return all_docs


def fetch_recently_archived_documents(days=7):
    if not READWISE_TOKEN:
        raise ValueError("Missing READWISE_TOKEN in environment variables. Ensure it's set in your .env file.")

    # Calculate the cutoff date (N days ago) - make it timezone-aware (UTC)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_date_iso = cutoff_date.isoformat()

    print(f"Fetching documents updated since: {cutoff_date_iso}")

    all_docs = []
    next_cursor = None

    while True:
        params = {
            "updatedAfter": cutoff_date_iso
        }
        if next_cursor:
            params["pageCursor"] = next_cursor

        print(f"Fetching page with params: {params}")

        try:
            response = requests.get(
                API_URL,
                headers={"Authorization": f"Token {READWISE_TOKEN}"},
                params=params,
                timeout=30
            )
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
            raise Exception(f"API Request Failed: {e}") from e

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            raise Exception("Failed to decode API response JSON.") from e

        results = data.get("results", [])
        all_docs.extend(results)
        next_cursor = data.get("nextPageCursor")

        print(f"Fetched {len(results)} documents. Total: {len(all_docs)}. Next cursor: {'Yes' if next_cursor else 'No'}")

        if not next_cursor:
            break

    # Filter for documents that are currently archived AND were moved to archive in the timeframe
    recently_archived = []

    for doc in all_docs:
        # Must be in archive location
        if doc.get("location") != "archive":
            continue

        last_moved_at = doc.get("last_moved_at")
        if last_moved_at:
            try:
                # Parse the last_moved_at timestamp - handle different formats
                if last_moved_at.endswith('Z'):
                    # Replace Z with +00:00 for proper ISO format
                    moved_date = datetime.fromisoformat(last_moved_at.replace('Z', '+00:00'))
                elif '+' in last_moved_at or last_moved_at.endswith('+00:00'):
                    # Already has timezone info
                    moved_date = datetime.fromisoformat(last_moved_at)
                else:
                    # Assume UTC if no timezone info
                    moved_date = datetime.fromisoformat(last_moved_at).replace(tzinfo=timezone.utc)

                # Check if it was moved within our timeframe
                if moved_date >= cutoff_date:
                    recently_archived.append(doc)

            except (ValueError, TypeError) as e:
                print(f"Warning: Could not parse date '{last_moved_at}' for document {doc.get('id', 'unknown')}: {e}")
                continue

    print(f"Found {len(recently_archived)} documents archived in the last {days} days")
    return recently_archived
