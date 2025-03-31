import os
import glob
import anthropic
from pathlib import Path
from datetime import datetime, timedelta, date
import calendar

def get_last_month_dates():
    """
    Get the date range for the previous month (all days)

    Returns:
        tuple: (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now()

    # Get the first day of the current month
    first_day_current_month = date(today.year, today.month, 1)

    # Get the last day of the previous month
    last_day_prev_month = first_day_current_month - timedelta(days=1)

    # Get the first day of the previous month
    first_day_prev_month = date(last_day_prev_month.year, last_day_prev_month.month, 1)

    return first_day_prev_month.strftime("%Y-%m-%d"), last_day_prev_month.strftime("%Y-%m-%d")

def get_month_name(date_str):
    """
    Get the month name from a date string in YYYY-MM-DD format

    Args:
        date_str (str): Date in YYYY-MM-DD format

    Returns:
        str: Month name (e.g., "January")
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%B %Y")

def get_last_month_notes(notes_dir="~/Obsidian/notes/recurring/daily/"):
    """
    Retrieve content from all notes of the previous month.

    Args:
        notes_dir (str): Directory path containing the notes

    Returns:
        str: Concatenated content of all notes from the previous month
    """
    notes_dir = os.path.expanduser(notes_dir)
    start_date, end_date = get_last_month_dates()

    # Get all files within the date range
    all_files = glob.glob(f"{notes_dir}/*.md")
    last_month_files = []

    for file in all_files:
        date_str = Path(file).stem  # Gets filename without extension
        if start_date <= date_str <= end_date:
            last_month_files.append(file)

    # Sort files by date
    last_month_files.sort()

    # Read content from all files
    all_content = []
    for file in last_month_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                date = Path(file).stem
                all_content.append(f"Date: {date}\n{content}\n---\n")
        except Exception as e:
            print(f"Error reading file {file}: {e}")

    return "\n".join(all_content)

def analyze_with_claude(content, month_name):
    """
    Send content to Claude API for analysis focused on blog-worthy themes.

    Args:
        content (str): The content to analyze
        month_name (str): Name of the month being analyzed

    Returns:
        str: AI-generated blog-ready summary of the month
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    client = anthropic.Client(api_key=api_key)

    prompt = f"""I'm writing a blog post about my activities and experiences in {month_name}. Based on my daily notes, help me identify meaningful themes and narratives rather than listing individual tasks.

Please analyze these daily notes and provide content in my voice (first person):

1. Major Themes (3-5)
   - What were the big patterns or storylines that defined my month?
   - How did these themes connect across different areas of my life?

2. Readwise Work Highlights
   • Theme 1: [Name of theme]
     - What I worked on and why it mattered to me
     - Key moments or milestones I reached
     - How I felt about it (if mentioned in the logs)

   • Theme 2: [Name of theme]
     - What I worked on and why it mattered to me
     - Key moments or milestones I reached
     - How I felt about it (if mentioned in the logs)

   (Add more themes as needed)

3. Personal Life Highlights
   • Side Projects
     - Project 1: [Project Name]
       * What I accomplished on this project
       * Challenges I overcame or insights I gained

     - Project 2: [Project Name]
       * What I accomplished on this project
       * Challenges I overcame or insights I gained

     (Include each project I worked on with its own bullet point)

   • Other Personal Theme: [Name of theme]
     - What this meant to me and how it developed
     - Memorable moments or realizations

   (Add more personal themes as needed)

4. Blog-Worthy Insights (4-6)
   • Insight 1: [Catchy title for the insight]
     - Here's a detailed exploration of this insight and why it resonated with me
     - I could expand this into a full section by discussing [specific examples from my notes]
     - Readers might connect with this because [reason], and they could apply it to their own lives by [practical application]

   • Insight 2: [Catchy title for the insight]
     - Here's a detailed exploration of this insight and why it resonated with me
     - I could expand this into a full section by discussing [specific examples from my notes]
     - This would make compelling content because [reason], and might spark interesting discussion around [related topic]

   (Continue with more detailed insights)

Write in my authentic voice - casual, reflective, and conversational. Focus on the meaningful stuff that would actually be interesting to read about, not just what filled my calendar.

Content:
{content}
"""

    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=2000,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error analyzing content with Claude: {e}"

def main():
    # Get content from last month's notes
    content = get_last_month_notes()

    if not content:
        print("No notes found for last month")
        return

    try:
        # Get date range for the header
        start_date, end_date = get_last_month_dates()
        month_name = get_month_name(start_date)

        # Analyze content with Claude
        summary = analyze_with_claude(content, month_name)

        # Print results
        print(f"\nBlog Post Material for {month_name}:")
        print("=" * 60)
        print(summary)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
