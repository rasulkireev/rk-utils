# TODOS
# - Split by type (pdf, epub, etc) , probbablty want to prioriztize articles and books

import requests
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
READWISE_TOKEN = os.getenv("READWISE_TOKEN")
API_URL = "https://readwise.io/api/v3/list/"
CUTOFF_DAYS = 7

def fetch_recent_documents():
    """Fetch all documents updated in the last 7 days"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=CUTOFF_DAYS)
    all_docs = []
    next_cursor = None

    while True:
        params = {"updatedAfter": cutoff.isoformat()}
        if next_cursor:
            params["pageCursor"] = next_cursor

        response = requests.get(
            API_URL,
            headers={"Authorization": f"Token {READWISE_TOKEN}"},
            params=params
        )

        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        data = response.json()
        all_docs.extend(data["results"])
        next_cursor = data.get("nextPageCursor")

        if not next_cursor:
            break

    # Filter to only include documents saved in the last 7 days
    recent_docs = [
        doc for doc in all_docs
        if doc.get("last_opened_at") and datetime.fromisoformat(doc.get("last_opened_at")).replace(tzinfo=timezone.utc) >= cutoff
    ]

    return recent_docs

def categorize_documents(documents):
    """Categorize documents by reading progress"""
    categories = {
        "not_started": [],
        "in_progress": [],
        "finished": []
    }

    for doc in documents:
        progress = doc.get("reading_progress", 0)

        if progress == 0:
            categories["not_started"].append(doc)
        elif progress >= 1:
            categories["finished"].append(doc)
        else:
            categories["in_progress"].append(doc)

    return categories

def format_tags(tags_dict):
    """Extract just tag names from the tags dictionary"""
    if not tags_dict:
        return "N/A"
    return ", ".join([tag_info.get("name", tag) for tag, tag_info in tags_dict.items()])

def format_field(value, default="N/A"):
    """Format a field for display"""
    if not value:
        return default
    if isinstance(value, list):
        return ", ".join(value) if value else default
    return str(value)

def print_summary(categories):
    """Print formatted summary of documents"""
    print(f"\n📚 Reading Summary (Last {CUTOFF_DAYS} Days)")
    print(f"----------------------------------")
    print(f"✅ Finished: {len(categories['finished'])}")
    print(f"🚧 In Progress: {len(categories['in_progress'])}")
    print(f"🆕 Not Started: {len(categories['not_started'])}\n")

    for category, docs in categories.items():
        if docs:
            print(f"\n{category.replace('_', ' ').title()}:")
            for doc in docs:
                progress = doc.get("reading_progress", 0) * 100
                print(f"\n- {doc.get('title', 'Untitled')}")
                print(f"  URL: {doc.get('url', 'No URL')}")
                print(f"  Progress: {progress:.0f}%")
                print(f"  Added: {doc.get('saved_at', 'Unknown date')[:10]}")
                print(f"  Last Opened: {doc.get('last_opened_at', 'Unknown date')[:10]}")
                print(f"  Category: {format_field(doc.get('category'))}")
                print(f"  Location: {format_field(doc.get('location'))}")
                print(f"  Author: {format_field(doc.get('author'))}")
                print(f"  Source: {format_field(doc.get('source'))}")
                print(f"  Summary: {format_field(doc.get('summary'))}")
                print(f"  Tags: {format_tags(doc.get('tags'))}")

if __name__ == "__main__":
    if not READWISE_TOKEN:
        raise ValueError("Missing READWISE_TOKEN in environment variables")

    print("Fetching your Readwise Reader documents...")
    documents = fetch_recent_documents()
    categories = categorize_documents(documents)
    print_summary(categories)
