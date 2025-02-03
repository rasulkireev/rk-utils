import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict

def fetch_highlights_2024():
    load_dotenv()
    token = os.getenv('READWISE_TOKEN')
    if not token:
        raise ValueError("READWISE_TOKEN not found in environment variables")

    def fetch_from_export_api():
        full_data = []
        next_page_cursor = None

        while True:
            params = {}
            if next_page_cursor:
                params['pageCursor'] = next_page_cursor

            response = requests.get(
                url="https://readwise.io/api/v2/export/",
                headers={"Authorization": f"Token {token}"},
                params=params
            )

            if response.status_code != 200:
                raise Exception(f"API request failed with status code: {response.status_code}")

            data = response.json()
            full_data.extend(data['results'])
            next_page_cursor = data.get('nextPageCursor')

            if not next_page_cursor:
                break

        return full_data

    return fetch_from_export_api()

def analyze_2024_activity(data):
    stats = {
        'total_books': 0,
        'total_highlights': 0,
        'highlights_by_month': defaultdict(int),
        'highlights_by_category': defaultdict(int),
        'books_by_category': defaultdict(set),
        'highlights_by_source': defaultdict(int),
        'most_highlighted_books': defaultdict(int),
        'total_notes': 0,
        'books_with_notes': set(),
        'favorite_highlights': 0
    }

    for book in data:
        book_highlights_2024 = []

        # Filter highlights from 2024
        for highlight in book['highlights']:
            if highlight.get('highlighted_at'):
                highlight_date = datetime.fromisoformat(highlight['highlighted_at'].replace('Z', '+00:00'))
                if highlight_date.year == 2024:
                    book_highlights_2024.append(highlight)

        if book_highlights_2024:
            stats['total_books'] += 1
            stats['total_highlights'] += len(book_highlights_2024)

            # Category stats
            category = book['category'] or 'uncategorized'
            stats['books_by_category'][category].add(book['title'])

            for highlight in book_highlights_2024:
                # Monthly distribution
                highlight_date = datetime.fromisoformat(highlight['highlighted_at'].replace('Z', '+00:00'))
                month = highlight_date.strftime('%B')
                stats['highlights_by_month'][month] += 1

                # Category distribution
                stats['highlights_by_category'][category] += 1

                # Source distribution
                stats['highlights_by_source'][book['source']] += 1

                # Book popularity
                stats['most_highlighted_books'][book['title']] += 1

                # Notes stats
                if highlight.get('note'):
                    stats['total_notes'] += 1
                    stats['books_with_notes'].add(book['title'])

                # Favorite highlights
                if highlight.get('is_favorite'):
                    stats['favorite_highlights'] += 1

    return stats

def format_number(num):
    return f"{num:,}"

def print_statistics(stats):
    print("\n📚 READWISE ACTIVITY SUMMARY 2024 📚")
    print("=" * 50)

    print("\n📊 OVERALL METRICS")
    print(f"Total books/articles with highlights: {stats['total_books']}")
    print(f"Total highlights made: {format_number(stats['total_highlights'])}")
    print(f"Total notes added: {format_number(stats['total_notes'])}")
    print(f"Favorite highlights: {format_number(stats['favorite_highlights'])}")

    print("\n📑 HIGHLIGHTS BY CATEGORY")
    print("-" * 40)
    for category, count in sorted(stats['highlights_by_category'].items(), key=lambda x: x[1], reverse=True):
        books_count = len(stats['books_by_category'][category])
        print(f"{category.title():15} : {count:5} highlights across {books_count:3} sources")

    print("\n📅 MONTHLY DISTRIBUTION")
    print("-" * 40)
    for month in ['January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']:
        if count := stats['highlights_by_month'].get(month, 0):
            print(f"{month:12} : {count:5} highlights")

    print("\n📖 TOP 5 MOST HIGHLIGHTED SOURCES")
    print("-" * 40)
    top_books = sorted(stats['most_highlighted_books'].items(), key=lambda x: x[1], reverse=True)[:5]
    for book, count in top_books:
        print(f"{book[:50]:52} : {count:3} highlights")

    print("\n🔍 SOURCE DISTRIBUTION")
    print("-" * 40)
    for source, count in sorted(stats['highlights_by_source'].items(), key=lambda x: x[1], reverse=True):
        print(f"{source:15} : {count:5} highlights")

def main():
    try:
        print("Fetching Readwise data...")
        data = fetch_highlights_2024()
        stats = analyze_2024_activity(data)
        print_statistics(stats)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
