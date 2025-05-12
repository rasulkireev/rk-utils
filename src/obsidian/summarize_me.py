import os
import glob
import argparse
from pathlib import Path
from google import genai
from typing import List, Dict

def get_all_recurring_notes(notes_base_dir: str = "~/Obsidian/notes/recurring/") -> Dict[str, List[str]]:
    """
    Retrieve content from all recurring notes (daily, weekly, monthly, yearly).

    Args:
        notes_base_dir (str): Base directory path containing the recurring notes

    Returns:
        Dict[str, List[str]]: Dictionary with directories as keys and lists of content as values
    """
    # Expand user path (~/)
    notes_base_dir = os.path.expanduser(notes_base_dir)

    # Subdirectories to check
    subdirs = ["daily", "weekly", "monthly", "yearly"]

    all_notes = {}

    for subdir in subdirs:
        dir_path = os.path.join(notes_base_dir, subdir)
        pattern = f"{dir_path}/*.md"

        # Get all matching files
        files = glob.glob(pattern)

        # Sort files by name
        files.sort()

        # Read content from all files
        contents = []
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = Path(file).stem  # Get filename without extension
                    contents.append(f"File: {filename}\n{content}\n---\n")
            except Exception as e:
                print(f"Error reading file {file}: {e}")

        if contents:
            all_notes[subdir] = contents

    return all_notes

def analyze_with_gemini(notes_data: Dict[str, List[str]]) -> str:
    """
    Send content to Gemini API for analysis.

    Args:
        notes_data (Dict[str, List[str]]): Dictionary with directories as keys and lists of content as values

    Returns:
        str: AI-generated summary about Rasul Kireev
    """
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    client = genai.Client(api_key=api_key)

    # Create a more structured prompt from the notes data
    prompt = "Please analyze the following notes (my journal entries) and extract any information about me (Rasul Kireev).\n"
    prompt += "Focus on personal details, interests, achievements, habits, goals, and any other relevant information.\n"
    prompt += "Please format the output as a comprehensive profile with categories and bullet points.\n\n"

    # Add content from each category
    for category, notes_list in notes_data.items():
        if notes_list:
            prompt += f"=== {category.upper()} NOTES ===\n"
            # Limit the number of notes to prevent token limits
            for note in notes_list[:20]:  # Take up to 20 notes from each category
                prompt += f"{note}\n"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro-preview-03-25", contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error analyzing content with Gemini: {e}"

def main():
    parser = argparse.ArgumentParser(description='Analyze recurring notes for information about Rasul Kireev')
    parser.add_argument('--notes-dir', type=str,
                       default="~/Obsidian/notes/recurring/",
                       help='Base directory containing the recurring notes')

    args = parser.parse_args()

    # Get content from all recurring notes
    notes_data = get_all_recurring_notes(args.notes_dir)

    if not notes_data:
        print("No notes found in any recurring directories")
        return

    try:
        # Analyze content with Gemini
        profile = analyze_with_gemini(notes_data)

        # Print results
        print("\nProfile of Rasul Kireev:")
        print("=" * 40)
        print(profile)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
