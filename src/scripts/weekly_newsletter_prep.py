import datetime
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Get your Readwise API token from https://readwise.io/access_token
READWISE_TOKEN = os.environ.get("READWISE_TOKEN")
if not READWISE_TOKEN:
    print("Error: Please set the READWISE_TOKEN environment variable.")
    exit()

def get_recent_highlights(token, days=7, sample_size=5):
    """
    Fetches highlights updated in the last specified number of days and returns a sample.

    Args:
        token: Your Readwise API token.
        days: The number of recent days to filter by.
        sample_size: The number of highlights to sample.

    Returns:
        A list of highlight dictionaries, or None if an error occurs.
    """
    url = "https://readwise.io/api/v2/highlights/"
    headers = {"Authorization": f"Token {token}"}
    now = datetime.datetime.now(datetime.timezone.utc)
    time_delta = datetime.timedelta(days=days)
    updated_after = (now - time_delta).isoformat()

    params = {
        "updated__gt": updated_after,
        "page_size": 100  # Adjust page size as needed
    }

    recent_highlights = []
    next_page = url

    try:
        while next_page:
            response = requests.get(next_page, headers=headers, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            recent_highlights.extend(data.get('results', []))
            next_page = data.get('next')
            params = {} # Clear params for subsequent pages

        if not recent_highlights:
            print(f"No highlights found updated in the last {days} days.")
            return []

        # Sample the highlights
        if len(recent_highlights) <= sample_size:
            return recent_highlights
        else:
            import random
            return random.sample(recent_highlights, sample_size)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching highlights: {e}")
        return None
    except ValueError:
        print("Error decoding JSON response.")
        return None

if __name__ == "__main__":
    recent_sample = get_recent_highlights(READWISE_TOKEN)

    if recent_sample:
        print("\nSample of recent highlights:")
        for i, highlight in enumerate(recent_sample):
            print(f"\n--- Highlight {i+1} ---")
            print(f"Text: {highlight.get('text')}")
            print(f"Book/Article: {highlight.get('title')}")
            print(f"Author: {highlight.get('author')}")
            print(f"Note: {highlight.get('note')}")
            print(f"Highlighted At: {highlight.get('highlighted_at')}")
