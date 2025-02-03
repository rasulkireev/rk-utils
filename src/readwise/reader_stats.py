import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict

def fetch_read_content_2024():
    load_dotenv()
    token = os.getenv('READWISE_TOKEN')
    if not token:
        raise ValueError("READWISE_TOKEN not found in environment variables")

    def fetch_reader_document_list_api(location='archive'):
        full_data = []
        next_page_cursor = None

        while True:
            params = {'location': location}
            if next_page_cursor:
                params['pageCursor'] = next_page_cursor

            response = requests.get(
                url="https://readwise.io/api/v3/list/",
                params=params,
                headers={"Authorization": f"Token {token}"},
            )

            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                break

            data = response.json()
            full_data.extend(data['results'])
            next_page_cursor = data.get('nextPageCursor')

            if not next_page_cursor:
                break

        return full_data

    archived_docs = fetch_reader_document_list_api()

    read_in_2024 = []
    for doc in archived_docs:
        last_moved_at = datetime.fromisoformat(doc['last_moved_at'].replace('Z', '+00:00'))
        if last_moved_at.year == 2024:
            read_in_2024.append({
                'title': doc['title'],
                'author': doc['author'] or 'Unknown',
                'category': doc['category'] or 'Uncategorized',
                'completed_date': last_moved_at,
                'word_count': doc['word_count'] or 0,  # Convert None to 0
                'reading_progress': doc.get('reading_progress', 0) or 0  # Convert None to 0
            })

    return read_in_2024

def calculate_statistics(content):
    stats = {
        'total_items': len(content),
        'by_category': defaultdict(int),
        'words_by_category': defaultdict(int),
        'by_month': defaultdict(int),
        'authors': defaultdict(int),
        'total_words': 0,
        'avg_words_per_item': 0,
        'completed_items': 0,
        'partially_read': 0,
        'items_with_word_count': 0  # New counter for items with valid word count
    }

    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    for item in content:
        # Category counts
        stats['by_category'][item['category']] += 1

        # Word counts by category (only if word_count exists)
        word_count = item['word_count']
        if word_count > 0:  # Only count if we have a valid word count
            stats['words_by_category'][item['category']] += word_count
            stats['total_words'] += word_count
            stats['items_with_word_count'] += 1

        # Monthly distribution
        month = item['completed_date'].month
        stats['by_month'][month_names[month]] += 1

        # Author statistics
        stats['authors'][item['author']] += 1

        # Reading progress
        progress = item['reading_progress']
        if progress >= 0.9:
            stats['completed_items'] += 1
        elif progress > 0:
            stats['partially_read'] += 1

    # Calculate averages (only for items with word count)
    if stats['items_with_word_count'] > 0:
        stats['avg_words_per_item'] = stats['total_words'] / stats['items_with_word_count']

    return stats

def format_number(num):
    return f"{num:,}"

def print_statistics(stats):
    print("\n📚 READING STATISTICS 2024 📚")
    print("=" * 50)

    print("\n📊 OVERALL METRICS")
    print(f"Total items: {stats['total_items']}")
    print(f"Items with word count: {stats['items_with_word_count']}")
    print(f"Total words read: {format_number(stats['total_words'])}")
    if stats['items_with_word_count'] > 0:
        print(f"Average words per item: {format_number(int(stats['avg_words_per_item']))}")
    print(f"Completed items: {stats['completed_items']}")
    print(f"Partially read items: {stats['partially_read']}")

    print("\n📑 BREAKDOWN BY CATEGORY")
    print("-" * 40)
    for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
        words = stats['words_by_category'][category]
        avg_words = words / count if count > 0 else 0
        print(f"{category.title():12} : {count:3} items | {format_number(words):10} words | avg: {format_number(int(avg_words))} words/item")

    print("\n📅 MONTHLY DISTRIBUTION")
    print("-" * 40)
    for month, count in sorted(stats['by_month'].items(), key=lambda x: list(stats['by_month'].keys()).index(x[0])):
        print(f"{month:12} : {count:3} items")

    print("\n✍️ TOP AUTHORS")
    print("-" * 40)
    top_authors = sorted(stats['authors'].items(), key=lambda x: x[1], reverse=True)[:5]
    for author, count in top_authors:
        if author != 'Unknown':  # Skip unknown authors
            print(f"{author[:30]:32} : {count:3} items")

    # Reading completion rate
    completion_rate = (stats['completed_items'] / stats['total_items'] * 100) if stats['total_items'] > 0 else 0
    print(f"\n📈 Completion Rate: {completion_rate:.1f}%")

def main():
    try:
        content = fetch_read_content_2024()
        stats = calculate_statistics(content)
        print_statistics(stats)

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise  # This will show the full error trace for debugging

if __name__ == "__main__":
    main()
