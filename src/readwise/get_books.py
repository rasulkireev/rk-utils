import os
from dotenv import load_dotenv
from collections import defaultdict

# Import the utility function
from src.readwise.utils import fetch_all_documents

# Load environment variables
load_dotenv()

# Configuration (API_URL and READWISE_TOKEN are now primarily used in utils.py)
# We still might need READWISE_TOKEN here if we add auth checks later
# READWISE_TOKEN = os.getenv("READWISE_TOKEN")

def get_books():
    """Fetch all PDF and EPUB documents using the utility function."""
    print("Fetching PDFs...")
    pdfs = fetch_all_documents(category='pdf')
    print(f"Fetched {len(pdfs)} PDFs.")

    print("Fetching EPUBs...")
    epubs = fetch_all_documents(category='epub')
    print(f"Fetched {len(epubs)} EPUBs.")

    return pdfs + epubs

def group_books_by_location(books):
    """Group books by their location."""
    grouped = defaultdict(list)
    for book in books:
        location = book.get('location', 'unknown')
        grouped[location].append(book)
    return grouped

def print_books_by_location(grouped_books):
    """Print books grouped by location."""
    # Define the desired order of locations
    location_order = ['new', 'later', 'shortlist', 'archive', 'feed', 'unknown']

    print("\n--- Books by Location ---")

    for location in location_order:
        books_in_location = grouped_books.get(location)
        if books_in_location:
            print(f"\n📍 Location: {location.capitalize()}")
            print("-" * (len(location) + 12))
            for book in books_in_location:
                title = book.get('title', 'Untitled')
                author = book.get('author', 'Unknown Author')
                print(f"- {title} - {author}")
        # else:
            # Optionally print if a location has no books
            # print(f"\n📍 Location: {location.capitalize()}")
            # print("-" * (len(location) + 12))
            # print("  (No books in this location)")


if __name__ == "__main__":
    try:
        print("Fetching your Readwise Reader books (PDFs and EPUBs)...")
        all_books = get_books()
        if not all_books:
            print("No PDF or EPUB documents found.")
        else:
            print(f"Total books fetched: {len(all_books)}") # Added total count
            grouped = group_books_by_location(all_books)
            print_books_by_location(grouped)
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
