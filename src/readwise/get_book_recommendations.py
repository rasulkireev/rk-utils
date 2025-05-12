import os
from google import genai
from dotenv import load_dotenv
from typing import List, Dict, Any

from src.readwise.utils import fetch_all_documents

# Load environment variables
load_dotenv()

def get_all_books() -> List[Dict[str, Any]]:
    """Fetch all PDF and EPUB documents from Readwise Reader."""
    print("Fetching PDFs from Readwise...")
    pdfs = fetch_all_documents(category='pdf')
    print(f"Fetched {len(pdfs)} PDFs.")

    print("Fetching EPUBs from Readwise...")
    epubs = fetch_all_documents(category='epub')
    print(f"Fetched {len(epubs)} EPUBs.")

    all_books = pdfs + epubs
    print(f"Total books (PDFs + EPUBs): {len(all_books)}")
    return all_books

def format_book_list(books: List[Dict[str, Any]]) -> str:
    """Formats the list of books into a string for the prompt."""
    formatted_list = []
    for book in books:
        title = book.get('title', 'Untitled')
        author = book.get('author', 'Unknown Author')
        formatted_list.append(f"- Title: {title}, Author: {author}")
    return "\n".join(formatted_list)

def get_recommendations_with_gemini(books: List[Dict[str, Any]]) -> str:
    """Get book recommendations from Gemini based on a list of books."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Ensure it's set in your .env file.")

    # Use genai.Client like in summarize_me.py
    client = genai.Client(api_key=api_key)

    # Define the model name (you can adjust this)
    model_name = "gemini-2.5-pro-preview-03-25"
    print(f"Using Gemini model: {model_name}")

    # Format the book list for the prompt
    book_list_str = format_book_list(books)
    if not book_list_str:
        return "No books provided to generate recommendations."

    # Construct the prompt
    prompt = (
        "Based on the following list of books I have saved in my Readwise Reader "
        "(which includes PDFs and EPUBs I intend to read (inbox and later) or have read (archive)), please provide 20 book recommendations, categorized as follows:\n\n"
        "1.  **Similar & Well-Known (5 books):** Popular books similar to those in my list that I might enjoy.\n"
        "2.  **Similar & Less-Known (5 books):** Hidden gems or less common books similar to those in my list.\n"
        "3.  **Different & Well-Known (5 books):** Popular books in genres or topics different from my usual reading, but which might expand my horizons.\n"
        "4.  **Different & Less-Known (5 books):** Niche or less common books in different genres/topics that could be interesting discoveries.\n\n"
        "For each recommendation, please include the title, author, and a brief (1-2 sentence) justification for why it fits the category and why I might like it.\n\n"
        "Here is my current list of books:\n"
        f"{book_list_str}\n\n"
        "Please format the output clearly with the four categories as headings.\n\n"
        "Recommendations:\n"
    )

    print("\nSending request to Gemini API...")
    # print(f"\n--- PROMPT START ---\n{prompt[:500]}...\n--- PROMPT END ---") # Debug: Print start of prompt

    try:
        # Simplified call structure, similar to summarize_me.py
        # Model name is passed directly, safety settings use defaults
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
            )

        # Simplified response handling
        recommendations = response.text

        print("Received recommendations from Gemini.")
        return recommendations

    except Exception as e:
        # Catching potential API errors or other issues
        print(f"Error generating recommendations with Gemini: {e}")
        # Attempt to get feedback if available (might not exist with client.models)
        # try:
        #     print(f"Gemini API Response Feedback: {response.prompt_feedback}")
        # except Exception:
        #     pass # Ignore if feedback isn't available
        return f"Error analyzing content with Gemini: {e}"

def main():
    try:
        print("Starting book recommendation process...")
        # 1. Fetch books from Readwise
        all_books = get_all_books()

        if not all_books:
            print("No books found in Readwise Reader (PDFs/EPUBs). Cannot generate recommendations.")
            return

        # 2. Get recommendations from Gemini
        recommendations = get_recommendations_with_gemini(all_books)

        # 3. Print results
        print("\n--- Book Recommendations from Gemini ---")
        print(recommendations)
        print("-----------------------------------------")

    except ValueError as e:
        # Specific handling for configuration errors (e.g., missing API keys)
        print(f"Configuration Error: {e}")
    except Exception as e:
        # General error handling
        print(f"An unexpected error occurred during the process: {e}")

if __name__ == "__main__":
    main()
