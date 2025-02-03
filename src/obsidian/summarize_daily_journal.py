import os
import glob
import argparse
from pathlib import Path
import anthropic

def get_notes_content(year, notes_dir="~/Obsidian/notes/recurring/daily/"):
    """
    Retrieve content from all notes of a specific year.

    Args:
        year (int): The year to filter notes
        notes_dir (str): Directory path containing the notes

    Returns:
        str: Concatenated content of all notes from the specified year
    """
    # Expand user path (~/)
    notes_dir = os.path.expanduser(notes_dir)

    # Create pattern for the specific year
    pattern = f"{notes_dir}/{year}-*.md"

    # Get all matching files
    files = glob.glob(pattern)

    # Sort files by date
    files.sort()

    # Read content from all files
    all_content = []
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                date = Path(file).stem  # Get filename without extension
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
        str: AI-generated summary of notable events
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    client = anthropic.Client(api_key=api_key)

    prompt = f"""Please analyze the following daily notes and create a list of notable events and important moments.
    Focus on key achievements, significant events, and memorable occasions.
    Please format the output as a bullet-point list.

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
    parser = argparse.ArgumentParser(description='Analyze daily notes from a specific year')
    parser.add_argument('year', type=int, help='Year to analyze')
    parser.add_argument('--notes-dir', type=str,
                       default="~/Obsidian/notes/recurring/daily/",
                       help='Directory containing the notes')

    args = parser.parse_args()

    # Get content from notes
    content = get_notes_content(args.year, args.notes_dir)

    if not content:
        print(f"No notes found for year {args.year}")
        return

    try:
        # Analyze content with Claude
        summary = analyze_with_claude(content)

        # Print results
        print(f"\nNotable Events from {args.year}:")
        print("=" * 40)
        print(summary)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
