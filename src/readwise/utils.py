import os
import requests
from dotenv import load_dotenv

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
