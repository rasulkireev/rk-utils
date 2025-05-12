import requests
import html
import time

USERNAME = "rasulkireev"
BASE_URL = "https://hn.algolia.com/api/v1/search"
OUTPUT_FILE = f"{USERNAME}_comments.txt"

def fetch_comments():
    """Fetches all comments for the specified user from the Algolia HN API."""
    all_comments = []
    page = 0
    total_pages = None

    print(f"Fetching comments for user: {USERNAME}")

    headers = {
        'User-Agent': 'My HN Comment Fetcher Script (Python/Requests)'
    }

    while True:
        params = {
            'tags': f'comment,author_{USERNAME}',
            'page': page
        }
        try:
            print(f"Fetching page {page}...", end="")
            response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            data = response.json()
            print(f" Done ({len(data.get('hits', []))} hits).")

            # --- Get total pages on the first request ---
            if total_pages is None:
                total_pages = data.get('nbPages', 0)
                nb_hits = data.get('nbHits', 0)
                if nb_hits == 0:
                    print("No comments found for this user.")
                    return []
                print(f"Total comments found: {nb_hits}")
                print(f"Total pages to fetch: {total_pages}")

            # --- Extract comments from the current page ---
            hits = data.get('hits', [])
            if not hits:
                print("No more hits found on this page or subsequent pages.")
                break # Stop if no hits are returned

            for hit in hits:
                comment_text = hit.get('comment_text')
                created_at = hit.get('created_at') # e.g., "2025-04-01T12:58:52Z"
                object_id = hit.get('objectID')

                if comment_text and created_at:
                    # Extract YYYY-MM-DD from the timestamp
                    date_str = created_at[:10]
                    # Decode HTML entities (like &#x2F;) and unicode escapes
                    cleaned_text = html.unescape(comment_text)
                    all_comments.append((date_str, cleaned_text, object_id))

            # --- Check if we've fetched all pages ---
            page += 1
            if page >= total_pages:
                print("Fetched all pages.")
                break

            # --- Add a small delay to be polite to the API ---
            time.sleep(0.5) # Sleep for 500 milliseconds

        except requests.exceptions.RequestException as e:
            print(f"\nError fetching page {page}: {e}")
            print("Stopping.")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred on page {page}: {e}")
            print("Stopping.")
            break # Stop on other unexpected errors

    return all_comments

def save_comments_to_file(comments):
    """Saves the fetched comments to a text file."""
    if not comments:
        print("No comments to save.")
        return

    print(f"Saving {len(comments)} comments to {OUTPUT_FILE}...")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # Sort comments by date (most recent first, based on typical API order)
            # If you need strict chronological order, you might need to sort explicitly
            # sorted_comments = sorted(comments, key=lambda x: x[0], reverse=True) # Example sorting

            for date_str, text, object_id in comments:
                 # Add a link back to the comment for context
                comment_link = f"https://news.ycombinator.com/item?id={object_id}"
                f.write(f"Date: {date_str}\n")
                f.write(f"Link: {comment_link}\n")
                f.write(f"Comment:\n{text}\n")
                f.write("-" * 20 + "\n\n") # Separator
        print("Successfully saved comments.")
    except IOError as e:
        print(f"Error writing to file {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    fetched_data = fetch_comments()
    save_comments_to_file(fetched_data)
