import os
import glob
import anthropic
from pathlib import Path
from datetime import datetime, timedelta

def get_last_week_dates():
    """
    Get the date range for last week (Monday through Sunday)

    Returns:
        tuple: (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now()
    last_sunday = today - timedelta(days=today.weekday() + 1)
    last_monday = last_sunday - timedelta(days=6)
    return last_monday.strftime("%Y-%m-%d"), last_sunday.strftime("%Y-%m-%d")

def get_last_week_notes(notes_dir="~/Obsidian/notes/recurring/daily/"):
    """
    Retrieve content from all notes of last week.

    Args:
        notes_dir (str): Directory path containing the notes

    Returns:
        str: Concatenated content of all notes from last week
    """
    notes_dir = os.path.expanduser(notes_dir)
    start_date, end_date = get_last_week_dates()

    # Get all files within the date range
    all_files = glob.glob(f"{notes_dir}/*.md")
    last_week_files = []

    for file in all_files:
        date_str = Path(file).stem  # Gets filename without extension
        if start_date <= date_str <= end_date:
            last_week_files.append(file)

    # Sort files by date
    last_week_files.sort()

    # Read content from all files
    all_content = []
    for file in last_week_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                date = Path(file).stem
                all_content.append(f"Date: {date}\n{content}\n---\n")
        except Exception as e:
            print(f"Error reading file {file}: {e}")

    return "\n".join(all_content)

def analyze_with_claude(content):
    """
    Send content to Claude API for analysis.

    Args:
        content (str): The content to analyze

    Returns:
        str: AI-generated summary of Readwise and Personal matters
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    client = anthropic.Client(api_key=api_key)

    prompt = f"""Analyze these daily notes and provide two brief summaries:

    1. Readwise Work
    - Key tasks and achievements related to Readwise

    2. Personal
    - Notable personal activities and events

    Use bullet points and be concise.

    Content:
    {content}"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1000,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error analyzing content with Claude: {e}"

def main():
    # Get content from last week's notes
    content = get_last_week_notes()

    if not content:
        print("No notes found for last week")
        return

    try:
        # Get date range for the header
        start_date, end_date = get_last_week_dates()

        # Analyze content with Claude
        summary = analyze_with_claude(content)

        # Print results
        print(f"\nWeekly Summary ({start_date} to {end_date}):")
        print("=" * 50)
        print(summary)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
