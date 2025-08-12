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
EXPORT_API_URL = "https://readwise.io/api/v2/export/"

def fetch_all_highlights(updated_after=None):
    """Fetch all highlights from the Readwise API using the export endpoint."""
    if not READWISE_TOKEN:
        raise ValueError("Missing READWISE_TOKEN in environment variables. Ensure it's set in your .env file.")

    all_data = []
    next_page_cursor = None

    print("Starting highlights fetch...")

    while True:
        params = {}
        if next_page_cursor:
            params['pageCursor'] = next_page_cursor
        if updated_after:
            params['updatedAfter'] = updated_after

        print(f"Fetching page with params: {params}")
        try:
            response = requests.get(
                EXPORT_API_URL,
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
        all_data.extend(results)
        next_page_cursor = data.get("nextPageCursor")

        total_highlights = sum(len(book.get('highlights', [])) for book in results)
        print(f"Fetched {len(results)} books with {total_highlights} highlights. Total books: {len(all_data)}. Next cursor: {'Yes' if next_page_cursor else 'No'}")

        if not next_page_cursor:
            break

    total_books = len(all_data)
    total_highlights = sum(len(book.get('highlights', [])) for book in all_data)
    print(f"Finished fetching. Total books: {total_books}, Total highlights: {total_highlights}")
    return all_data

def format_highlights_for_analysis(books_data: List[Dict], max_chars: int = 800000) -> str:
    """Format highlights into a readable string for Gemini analysis with size limit."""
    formatted_text = ""

    # Calculate totals
    total_books = len(books_data)
    total_highlights = sum(len(book.get('highlights', [])) for book in books_data)

    formatted_text += f"Total books/sources analyzed: {total_books}\n"
    formatted_text += f"Total highlights analyzed: {total_highlights}\n\n"

    # Group by category for better organization
    categories = {}
    for book in books_data:
        category = book.get('category', 'unknown')
        if category not in categories:
            categories[category] = []
        categories[category].append(book)

    for category, category_books in categories.items():
        category_highlights = sum(len(book.get('highlights', [])) for book in category_books)
        formatted_text += f"=== {category.upper()} ({len(category_books)} sources, {category_highlights} highlights) ===\n\n"

        for book in category_books:
            highlights = book.get('highlights', [])
            if not highlights:
                continue

            # Check if we're approaching the character limit
            if len(formatted_text) > max_chars:
                formatted_text += "\n[TRUNCATED - Too many highlights to include all details]\n"
                return formatted_text

            title = book.get('title', 'Unknown Title')
            author = book.get('author', 'Unknown Author')
            source = book.get('source', '')
            source_url = book.get('source_url', '')
            book_tags = book.get('book_tags', [])

            formatted_text += f"--- {title}"
            if author and author != 'Unknown Author':
                formatted_text += f" by {author}"
            formatted_text += f" ({len(highlights)} highlights) ---\n"

            if source:
                formatted_text += f"Source: {source}\n"
            if source_url:
                formatted_text += f"URL: {source_url}\n"
            if book_tags:
                tag_names = [tag.get('name', tag) if isinstance(tag, dict) else str(tag) for tag in book_tags]
                formatted_text += f"Book Tags: {', '.join(tag_names)}\n"

            formatted_text += "\n"

            # Sort highlights by location if available
            sorted_highlights = sorted(highlights, key=lambda h: h.get('location', 0) or 0)

            for highlight in sorted_highlights:
                if len(formatted_text) > max_chars:
                    formatted_text += "\n[TRUNCATED - Character limit reached]\n"
                    return formatted_text

                text = highlight.get('text', '').strip()
                note = highlight.get('note', '').strip()
                location = highlight.get('location')
                color = highlight.get('color', '')
                highlighted_at = highlight.get('highlighted_at', '')
                tags = highlight.get('tags', [])
                is_favorite = highlight.get('is_favorite', False)

                if not text:
                    continue

                formatted_text += f"• {text}\n"

                if note:
                    formatted_text += f"  📝 Note: {note}\n"

                details = []
                if location:
                    details.append(f"Location: {location}")
                if color:
                    details.append(f"Color: {color}")
                if is_favorite:
                    details.append("⭐ Favorite")
                if highlighted_at:
                    try:
                        # Parse and format the date
                        dt = datetime.fromisoformat(highlighted_at.replace('Z', '+00:00'))
                        details.append(f"Date: {dt.strftime('%Y-%m-%d')}")
                    except:
                        details.append(f"Date: {highlighted_at}")

                if details:
                    formatted_text += f"  ({' | '.join(details)})\n"

                if tags:
                    tag_names = [tag.get('name', tag) if isinstance(tag, dict) else str(tag) for tag in tags]
                    if tag_names:
                        formatted_text += f"  🏷️ Tags: {', '.join(tag_names)}\n"

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
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents="Hello, this is a test. Please respond with 'API key is working'."
        )
        print(f"✓ Gemini API connection successful: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"✗ Gemini API connection failed: {e}")
        return False

def analyze_highlights_with_gemini(highlights_text: str) -> str:
    """Use Gemini to analyze highlights and create a comprehensive personality profile."""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Ensure it's set in your .env file.")

    client = genai.Client(api_key=GOOGLE_API_KEY)
    model_name = "gemini-2.5-pro"

    print(f"Using Gemini model: {model_name}")

    prompt = f"""
Based on the following comprehensive collection of highlights from my Readwise account, please create the most detailed and insightful profile of me as a person that you possibly can. These highlights represent passages I found meaningful enough to save while reading books, articles, tweets, and other content.

## PART 1: COMPREHENSIVE PERSONAL PROFILE

Tell me everything about myself that you can possibly infer from this dataset. Here are some dimensions to consider, but please include anything else you can deduce:

**Demographics & Life Situation:**
- Approximate age range and generation
- Likely gender/sex
- Geographic location or region
- Education level and background
- Industry/field of work
- Job level/seniority/career stage
- Approximate income bracket or socioeconomic status
- Relationship status and family situation
- Parental status and children's ages (if applicable)

**Personality & Psychology:**
- Core personality traits and psychological patterns
- Values, beliefs, and philosophical leanings
- Political orientation and social views
- Risk tolerance and decision-making style
- Emotional patterns and psychological needs
- Strengths, weaknesses, and blind spots
- Major life transitions or phases I might be going through

**Lifestyle & Habits:**
- Learning style and information consumption patterns
- Health concerns or wellness focus areas
- Hobbies, interests, and recreational activities
- Social patterns and relationship approaches
- Time management and productivity approaches
- Seasonal patterns in interests or behavior
- Technology usage and digital habits

**Intellectual Profile:**
- Cognitive style and thinking patterns
- Areas of expertise or deep knowledge
- Intellectual curiosities and learning goals
- Problem-solving approaches
- Creative vs. analytical tendencies

## PART 2: DETAILED RECOMMENDATIONS

Based on your analysis, provide comprehensive recommendations in these categories:

**📚 READING RECOMMENDATIONS (15-20 items):**
- Books that would expand my thinking or fill knowledge gaps
- Articles, essays, or papers I should read
- Authors I should explore further
- Specific topics or fields I should investigate
- Mix of challenging and accessible content

**🎯 ACTIVITIES & EXPERIENCES TO TRY (10-15 items):**
- Hobbies or activities that align with my interests
- Skills I should develop
- Experiences that would broaden my perspective
- Communities or groups I should join
- Courses or learning opportunities
- Travel destinations or cultural experiences

**🤔 THINGS TO THINK ABOUT & EXPLORE (10-12 items):**
- Important questions I should be asking myself
- Philosophical or existential topics to contemplate
- Areas where I might want to challenge my assumptions
- Personal development areas to focus on
- Relationships or life decisions to consider
- Future planning or goal-setting areas

**🔍 BLIND SPOTS & GROWTH AREAS:**
- Perspectives or viewpoints I might be missing
- Areas where I could benefit from more diverse input
- Potential biases or limitations in my thinking
- Skills or knowledge areas that would complement my existing interests

## ANALYSIS GUIDELINES:

- Be specific and reference actual highlighted passages to support your inferences
- Look for patterns across different sources and time periods
- Pay attention to what I choose to highlight vs. what I choose to annotate
- Consider the evolution of my interests over time
- Be honest and insightful - I want genuine assessment, not flattery
- Make educated guesses where evidence suggests certain conclusions
- Acknowledge uncertainty where the data is ambiguous
- Focus on actionable insights and practical recommendations

Here are my highlights:

{highlights_text}

Please provide a comprehensive, thoughtful analysis that treats this as a serious profiling and recommendation exercise. I want to learn as much as possible about myself and get genuinely useful suggestions for my continued growth and exploration.
"""

    print("\nSending request to Gemini API for comprehensive personality analysis...")
    print(f"Analyzing approximately {len(highlights_text):,} characters of highlight data...")

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

        if "API key" in str(e).lower() or "expired" in str(e).lower():
            print("\n🔑 API Key Issue Detected!")
            print("Please:")
            print("1. Go to https://aistudio.google.com/app/apikey")
            print("2. Create a new API key")
            print("3. Update your .env file with the new key")
            print("4. Restart the script")

        return f"Error analyzing highlights with Gemini: {e}"

def save_analysis_to_file(analysis: str, filename: str = None):
    """Save the analysis to a file with timestamp."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"readwise_comprehensive_profile_{timestamp}.md"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive Readwise Highlights Profile & Recommendations\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("*This comprehensive analysis is based on the passages you chose to highlight while reading, ")
            f.write("which reveals deep insights into your demographics, personality, values, thinking patterns, and life situation. ")
            f.write("It includes detailed recommendations for books, activities, and areas of exploration.*\n\n")
            f.write("---\n\n")
            f.write(analysis)

        print(f"\nAnalysis saved to: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving analysis to file: {e}")
        return None

def generate_highlights_summary(books_data: List[Dict]) -> Dict[str, Any]:
    """Generate a summary of the highlights data."""
    total_books = len(books_data)
    total_highlights = sum(len(book.get('highlights', [])) for book in books_data)

    # Category breakdown
    categories = {}
    for book in books_data:
        category = book.get('category', 'unknown')
        if category not in categories:
            categories[category] = {'books': 0, 'highlights': 0}
        categories[category]['books'] += 1
        categories[category]['highlights'] += len(book.get('highlights', []))

    # Most highlighted books
    books_by_highlights = sorted(books_data, key=lambda b: len(b.get('highlights', [])), reverse=True)
    top_books = books_by_highlights[:10]

    # Collect all tags
    all_tags = set()
    for book in books_data:
        for highlight in book.get('highlights', []):
            for tag in highlight.get('tags', []):
                tag_name = tag.get('name', tag) if isinstance(tag, dict) else str(tag)
                all_tags.add(tag_name)

    # Time analysis
    highlight_dates = []
    for book in books_data:
        for highlight in book.get('highlights', []):
            date_str = highlight.get('highlighted_at')
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    highlight_dates.append(dt)
                except:
                    pass

    return {
        'total_books': total_books,
        'total_highlights': total_highlights,
        'categories': categories,
        'top_books': [(book.get('title', 'Unknown'), book.get('author', 'Unknown'), len(book.get('highlights', []))) for book in top_books],
        'total_tags': len(all_tags),
        'tags': sorted(list(all_tags)),
        'date_range': {
            'earliest': min(highlight_dates) if highlight_dates else None,
            'latest': max(highlight_dates) if highlight_dates else None,
            'total_dates': len(highlight_dates)
        }
    }

def main():
    """Main function to orchestrate the comprehensive highlights-based analysis."""
    print("=== Comprehensive Readwise Highlights Profile & Recommendations ===\n")

    # Test API connections first
    print("Testing API connections...")
    if not test_gemini_connection():
        print("❌ Cannot proceed without working Gemini API key.")
        return

    try:
        # Fetch all highlights
        print("\nStep 1: Fetching all highlights from Readwise...")
        books_data = fetch_all_highlights()

        # Check if we have any highlights
        total_highlights = sum(len(book.get('highlights', [])) for book in books_data)
        if total_highlights == 0:
            print("No highlights found. Please check your Readwise token and ensure you have highlights saved.")
            return

        # Generate summary
        print(f"\nStep 2: Analyzing {len(books_data)} books with {total_highlights} highlights...")
        summary = generate_highlights_summary(books_data)

        print(f"\n📊 HIGHLIGHTS SUMMARY:")
        print(f"   • Total sources: {summary['total_books']}")
        print(f"   • Total highlights: {summary['total_highlights']}")

        # Fix the problematic line by building the string differently
        category_strings = []
        for cat, data in summary['categories'].items():
            category_strings.append(f"{cat} ({data['highlights']} highlights)")
        print(f"   • Categories: {', '.join(category_strings)}")

        print(f"   • Total tags used: {summary['total_tags']}")

        if summary['date_range']['earliest'] and summary['date_range']['latest']:
            print(f"   • Date range: {summary['date_range']['earliest'].strftime('%Y-%m-%d')} to {summary['date_range']['latest'].strftime('%Y-%m-%d')}")

        if summary['top_books']:
            print(f"\n📚 Most highlighted sources:")
            for i, (title, author, count) in enumerate(summary['top_books'][:5], 1):
                print(f"   {i}. {title} by {author} ({count} highlights)")

        # Format highlights for analysis
        print(f"\nStep 3: Formatting highlights for comprehensive analysis...")
        formatted_highlights = format_highlights_for_analysis(books_data)

        # Show a preview
        print(f"Highlights data preview (first 500 chars):")
        print("-" * 50)
        print(formatted_highlights[:500] + "..." if len(formatted_highlights) > 500 else formatted_highlights)
        print("-" * 50)

        print(f"\nStep 4: Sending to Gemini for comprehensive personality analysis and recommendations...")
        analysis = analyze_highlights_with_gemini(formatted_highlights)

        # Check if analysis was successful
        if analysis.startswith("Error analyzing"):
            print("❌ Analysis failed. Please check the error message above.")
            return

        print("\nStep 5: Saving comprehensive analysis...")
        filename = save_analysis_to_file(analysis)

        print("\n" + "="*80)
        print("COMPREHENSIVE HIGHLIGHTS PROFILE & RECOMMENDATIONS COMPLETE")
        print("="*80)
        print(analysis)

        if filename:
            print(f"\n(Full analysis also saved to: {filename})")

    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()
