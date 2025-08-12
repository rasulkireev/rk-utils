# remove the demographic stuff. useless....

# recommendations should be to challenge my thinking in terms of my blind spots.
# when ai figures out my weaknesses i want to improve those

import os
import requests
from dotenv import load_dotenv
from google import genai
from typing import List, Dict, Any
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
READWISE_TOKEN = os.getenv("READWISE_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
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
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text[:500]}...")
            raise Exception("Failed to decode API response JSON.") from e

        results = data.get("results", [])
        all_docs.extend(results)
        next_cursor = data.get("nextPageCursor")

        print(f"Fetched {len(results)} documents. Total: {len(all_docs)}. Next cursor: {'Yes' if next_cursor else 'No'}")

        if not next_cursor:
            break

    print(f"Finished fetching. Total documents: {len(all_docs)}")
    return all_docs

def fetch_documents_by_locations(locations: List[str]) -> Dict[str, List[Dict]]:
    """Fetch documents from multiple locations and organize them by location."""
    documents_by_location = {}

    for location in locations:
        print(f"\n--- Fetching documents from '{location}' ---")
        try:
            docs = fetch_all_documents(location=location)
            documents_by_location[location] = docs
            print(f"Found {len(docs)} documents in '{location}'")
        except Exception as e:
            print(f"Error fetching documents from '{location}': {e}")
            documents_by_location[location] = []

    return documents_by_location

def format_documents_for_analysis(documents_by_location: Dict[str, List[Dict]], max_chars: int = 800000) -> str:
    """Format documents into a readable string for Gemini analysis with size limit."""
    formatted_text = ""

    total_docs = sum(len(docs) for docs in documents_by_location.values())
    formatted_text += f"Total documents analyzed: {total_docs}\n\n"

    for location, docs in documents_by_location.items():
        if not docs:
            continue

        formatted_text += f"=== {location.upper()} ({len(docs)} documents) ===\n\n"

        # Group by category for better organization
        categories = {}
        for doc in docs:
            category = doc.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(doc)

        for category, category_docs in categories.items():
            formatted_text += f"--- {category.upper()} ({len(category_docs)} items) ---\n"

            for doc in category_docs:
                # Check if we're approaching the character limit
                if len(formatted_text) > max_chars:
                    formatted_text += "\n[TRUNCATED - Too many documents to include all details]\n"
                    return formatted_text

                title = doc.get('title', 'No title')
                author = doc.get('author', 'Unknown author')
                site_name = doc.get('site_name', '')
                summary = doc.get('summary', '')
                word_count = doc.get('word_count', 0)
                reading_progress = doc.get('reading_progress', 0)
                tags = doc.get('tags', {})
                published_date = doc.get('published_date', '')

                formatted_text += f"• {title}"
                if author and author != 'Unknown author':
                    formatted_text += f" by {author}"
                if site_name:
                    formatted_text += f" ({site_name})"
                formatted_text += "\n"

                if summary:
                    formatted_text += f"  Summary: {summary[:200]}{'...' if len(summary) > 200 else ''}\n"

                if word_count:
                    formatted_text += f"  Length: {word_count} words"
                    if reading_progress > 0:
                        formatted_text += f" (Read: {int(reading_progress * 100)}%)"
                    formatted_text += "\n"

                if tags:
                    tag_names = [tag.get('name', key) for key, tag in tags.items()]
                    if tag_names:
                        formatted_text += f"  Tags: {', '.join(tag_names)}\n"

                if published_date:
                    formatted_text += f"  Published: {published_date}\n"

                formatted_text += "\n"

            formatted_text += "\n"

        formatted_text += "\n"

    return formatted_text

def test_gemini_connection():
    """Test if the Gemini API key is working."""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        # Test with a simple request
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents="Hello, this is a test. Please respond with 'API key is working'."
        )
        print(f"✓ Gemini API connection successful: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"✗ Gemini API connection failed: {e}")
        return False

def analyze_reading_profile_with_gemini(documents_text: str) -> str:
    """Use Gemini to analyze reading habits and create a comprehensive personality profile."""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Ensure it's set in your .env file.")

    client = genai.Client(api_key=GOOGLE_API_KEY)
    # Use a more recent and stable model
    model_name = "gemini-2.5-pro"

    print(f"Using Gemini model: {model_name}")

    prompt = f"""
Based on the following comprehensive list of documents from my Readwise Reader (organized by inbox, later, and archive), please create a detailed personality and intellectual profile of me as a person.

Please analyze and provide insights on:

## PART 1: INTELLECTUAL & PERSONALITY PROFILE

1. **Intellectual Interests & Curiosity Patterns:**
   - What subjects and topics am I most drawn to?
   - What does my reading diversity (or lack thereof) say about my intellectual curiosity?
   - Are there any emerging or evolving interests I can identify?

2. **Learning Style & Information Consumption:**
   - How do I seem to consume information (long-form vs short articles, academic vs popular content)?
   - What's my apparent relationship with different media types (articles, PDFs, videos, etc.)?
   - Do I seem to be a completionist reader or a browser/sampler?

3. **Values & Worldview Indicators:**
   - What values or philosophical leanings can you infer from my reading choices?
   - What seems to matter to me based on the topics I save and engage with?
   - Are there any ideological patterns or blind spots you can identify?

4. **Professional & Personal Development Focus:**
   - What areas am I likely trying to develop or improve in?
   - What does my reading suggest about my career interests or professional goals?
   - Are there patterns suggesting personal growth areas I'm working on?

5. **Personality Traits & Behavioral Patterns:**
   - Based on my reading habits, what personality traits can you infer?
   - How do I seem to approach learning and knowledge acquisition?
   - What does my organization system (inbox/later/archive) suggest about my habits?

## PART 2: DEMOGRAPHIC & LIFESTYLE PROFILE

Tell me everything about myself that you can possibly infer from this dataset. Please analyze and make educated guesses about:

- **Age range** (and reasoning)
- **Gender/sex** (if inferable)
- **Geographic location** (country, region, or city if possible)
- **Education level** (degree type, field of study)
- **Industry/field of work** (specific role if possible)
- **Job level/seniority** (entry, mid, senior, executive)
- **Income bracket** (rough estimate with reasoning)
- **Political orientation** (if discernible)
- **Risk tolerance** (conservative, moderate, aggressive)
- **Learning style** (visual, auditory, kinesthetic, reading/writing)
- **Information diet** (news sources, content types, frequency)
- **Relationship status** (single, partnered, married)
- **Parental status** (children yes/no, approximate ages if inferable)
- **Health concerns** (physical, mental, wellness interests)
- **Major life transitions** (career changes, moves, life events)
- **Seasonal patterns** in interests or reading habits
- **Time management style** (organized, spontaneous, etc.)
- **Social preferences** (introverted, extroverted, community involvement)
- **Technology adoption** (early adopter, mainstream, laggard)
- **Financial interests** (investing, budgeting, entrepreneurship)
- **Hobbies and interests** outside of reading

For each inference, please provide your reasoning based on specific evidence from my reading patterns.

## PART 3: RECOMMENDATIONS

Based on your analysis, please provide comprehensive recommendations:

### Books to Read:
- 5-10 specific book recommendations with titles and authors
- Explain why each book would be valuable for me specifically
- Include a mix of genres/topics that would expand my horizons

### Articles/Content to Explore:
- Specific publications, newsletters, or content creators I should follow
- Topics or perspectives I might be missing
- Emerging areas that align with my interests

### Hobbies/Activities to Try:
- Physical activities or sports
- Creative pursuits
- Social activities or communities to join
- Skills to develop
- Experiences to seek out

### Things to Think About:
- Important questions I should be asking myself
- Potential blind spots in my thinking
- Areas for personal growth or development
- Career or life decisions to consider
- Relationships or social connections to nurture

### Potential Blind Spots & Growth Areas:
- What perspectives or areas might I be missing?
- What recommendations would you make to broaden or deepen my intellectual diet?
- Are there any concerning patterns or areas for improvement?

Please be specific and reference actual titles, authors, or topics from my reading list to support your analysis. Be honest and insightful - I want a genuine assessment, not just flattery. Make your demographic inferences as specific as possible while acknowledging uncertainty where appropriate.

Here is my reading data:

{documents_text}

Please provide a comprehensive, thoughtful analysis that treats this as a serious intellectual and personal profiling exercise.
"""

    print("\nSending request to Gemini API for comprehensive personality analysis...")
    print(f"Analyzing approximately {len(documents_text):,} characters of reading data...")

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        analysis = response.text
        print("Received comprehensive personality analysis from Gemini.")
        return analysis

    except Exception as e:
        print(f"Error generating analysis with Gemini: {e}")

        # Check if it's an API key issue
        if "API key" in str(e).lower() or "expired" in str(e).lower():
            print("\n🔑 API Key Issue Detected!")
            print("Please:")
            print("1. Go to https://aistudio.google.com/app/apikey")
            print("2. Create a new API key")
            print("3. Update your .env file with the new key")
            print("4. Restart the script")

        return f"Error analyzing reading profile with Gemini: {e}"

def save_analysis_to_file(analysis: str, filename: str = None):
    """Save the analysis to a file with timestamp."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"readwise_comprehensive_analysis_{timestamp}.md"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive Readwise Reader Analysis\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("This analysis includes personality profiling, demographic inferences, and personalized recommendations based on reading patterns.\n\n")
            f.write("---\n\n")
            f.write(analysis)

        print(f"\nAnalysis saved to: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving analysis to file: {e}")
        return None

def main():
    """Main function to orchestrate the comprehensive personality analysis."""
    print("=== Comprehensive Readwise Reader Analysis ===\n")
    print("This will analyze your reading patterns to create a detailed personality profile,")
    print("make demographic inferences, and provide personalized recommendations.\n")

    # Test API connections first
    print("Testing API connections...")
    if not test_gemini_connection():
        print("❌ Cannot proceed without working Gemini API key.")
        return

    # Define the locations we want to analyze
    locations_to_analyze = ['new', 'later', 'archive']  # 'new' is inbox

    try:
        # Fetch documents from all specified locations
        print("\nStep 1: Fetching documents from Readwise Reader...")
        documents_by_location = fetch_documents_by_locations(locations_to_analyze)

        # Check if we have any documents
        total_docs = sum(len(docs) for docs in documents_by_location.values())
        if total_docs == 0:
            print("No documents found. Please check your Readwise token and ensure you have documents saved.")
            return

        print(f"\nStep 2: Formatting {total_docs} documents for analysis...")
        formatted_documents = format_documents_for_analysis(documents_by_location)

        # Show a preview of what we're analyzing
        print(f"Document data preview (first 500 chars):")
        print("-" * 50)
        print(formatted_documents[:500] + "..." if len(formatted_documents) > 500 else formatted_documents)
        print("-" * 50)

        print(f"\nStep 3: Sending to Gemini for comprehensive analysis...")
        print("This may take a moment as we're generating a detailed profile...")
        analysis = analyze_reading_profile_with_gemini(formatted_documents)

        # Check if analysis was successful
        if analysis.startswith("Error analyzing"):
            print("❌ Analysis failed. Please check the error message above.")
            return

        print("\nStep 4: Saving analysis...")
        filename = save_analysis_to_file(analysis)

        print("\n" + "="*60)
        print("COMPREHENSIVE ANALYSIS COMPLETE")
        print("="*60)
        print(analysis)

        if filename:
            print(f"\n(Full analysis also saved to: {filename})")

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()
