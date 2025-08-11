import os
from dotenv import load_dotenv
import datetime
import requests
from typing import List, Dict, Any, Optional

# Load environment variables early
load_dotenv()

# Configuration
READWISE_TOKEN = os.getenv("READWISE_TOKEN")
API_URL = "https://readwise.io/api/v3/list/"


def get_highlights_last_7_days() -> List[Dict[str, Any]]:
    """
    Fetch all highlights that were updated in the last 7 days from Readwise.

    Args:
        token (str): Your Readwise access token

    Returns:
        List[Dict[str, Any]]: List of all highlights from the last 7 days
    """
    # Calculate the date 7 days ago
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    updated_after = seven_days_ago.isoformat()

    all_highlights = []
    next_page_cursor = None

    while True:
        # Prepare request parameters
        params = {'updatedAfter': updated_after}
        if next_page_cursor:
            params['pageCursor'] = next_page_cursor

        try:
            # Make the API request
            response = requests.get(
                url="https://readwise.io/api/v2/export/",
                params=params,
                headers={"Authorization": f"Token {READWISE_TOKEN}"},
                verify=True
            )

            # Check if request was successful
            response.raise_for_status()

            # Parse the JSON response
            data = response.json()

            # Extract highlights from all books in this page
            for book in data.get('results', []):
                highlights = book.get('highlights', [])
                # Add book metadata to each highlight for context
                for highlight in highlights:
                    highlight['book_title'] = book.get('title', '')
                    highlight['book_author'] = book.get('author', '')
                    highlight['book_category'] = book.get('category', '')
                    highlight['book_source'] = book.get('source', '')

                all_highlights.extend(highlights)

            # Check if there are more pages
            next_page_cursor = data.get('nextPageCursor')
            if not next_page_cursor:
                break

        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            break
        except KeyError as e:
            print(f"Error parsing response: {e}")
            break

    return all_highlights

def filter_highlights_by_date_range(highlights: List[Dict[str, Any]],
                                  days: int = 7) -> List[Dict[str, Any]]:
    """
    Filter highlights to only include those highlighted (not just updated)
    in the last N days.

    Args:
        highlights: List of highlight dictionaries
        days: Number of days to look back (default: 7)

    Returns:
        List of highlights that were actually made in the last N days
    """
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)

    filtered_highlights = []
    for highlight in highlights:
        highlighted_at = highlight.get('highlighted_at')
        if highlighted_at:
            try:
                # Parse the ISO format datetime
                highlight_date = datetime.datetime.fromisoformat(
                    highlighted_at.replace('Z', '+00:00')
                )
                # Convert to local timezone for comparison
                highlight_date = highlight_date.replace(tzinfo=None)

                if highlight_date >= cutoff_date:
                    filtered_highlights.append(highlight)
            except (ValueError, TypeError):
                # Skip highlights with invalid dates
                continue

    return filtered_highlights


def main():
    try:
        # Get all highlights updated in the last 7 days
        recent_highlights = get_highlights_last_7_days()

        # Optional: Filter to only highlights actually made in the last 7 days
        # (not just updated in the last 7 days)
        actually_recent = filter_highlights_by_date_range(recent_highlights, days=7)

        print(f"\nFound {len(recent_highlights)} highlights updated in the last 7 days")
        print(f"Found {len(actually_recent)} highlights actually made in the last 7 days")

        # Display some example highlights
        for i, highlight in enumerate(actually_recent[:3]):  # Show first 3
            print(f"\n--- Highlight {i+1} ---")
            print(f"Book: {highlight.get('book_title', 'Unknown')}")
            print(f"Author: {highlight.get('book_author', 'Unknown')}")
            print(f"Text: {highlight.get('text', '')[:100]}...")
            print(f"Highlighted at: {highlight.get('highlighted_at', 'Unknown')}")
            if highlight.get('note'):
                print(f"Note: {highlight.get('note')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
