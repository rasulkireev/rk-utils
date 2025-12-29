import os
import glob
import argparse
from pathlib import Path
from datetime import datetime, date


def get_readwise_work_dates(start_date=None):
    """
    Get the date range from start_date to today

    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format.
                                    Defaults to "2024-10-01"

    Returns:
        tuple: (start_date, end_date) in YYYY-MM-DD format
    """
    if start_date is None:
        start_date = "2024-10-01"
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")
    return start_date, end_date


def get_readwise_work_notes(notes_dir="~/Obsidian/notes/recurring/daily/", start_date=None):
    """
    Retrieve content from all notes from start_date onwards.

    Args:
        notes_dir (str): Directory path containing the notes
        start_date (str, optional): Start date in YYYY-MM-DD format.
                                    Defaults to "2024-10-01"

    Returns:
        str: Concatenated content of all relevant notes
    """
    notes_dir = os.path.expanduser(notes_dir)
    start_date, end_date = get_readwise_work_dates(start_date)

    # Get all files within the date range
    all_files = glob.glob(f"{notes_dir}/*.md")
    relevant_files = []

    for file in all_files:
        date_str = Path(file).stem  # Gets filename without extension
        if start_date <= date_str <= end_date:
            relevant_files.append(file)

    # Sort files by date
    relevant_files.sort()

    print(f"Found {len(relevant_files)} journal entries from {start_date} to {end_date}")

    # Read content from all files
    all_content = []
    for file in relevant_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

                # Filter out personal content and everything below it
                filtered_content = filter_work_content(content)

                if filtered_content.strip():  # Only add if there's meaningful content
                    date = Path(file).stem
                    all_content.append(f"Date: {date}\n{filtered_content}\n---\n")
        except Exception as e:
            print(f"Error reading file {file}: {e}")

    return "\n".join(all_content)


def filter_work_content(content):
    """
    Filter out personal content and everything below it from daily notes.

    Args:
        content (str): Raw content from a daily note file

    Returns:
        str: Filtered content with only work-related sections
    """
    lines = content.split('\n')
    filtered_lines = []

    for line in lines:
        # Stop processing when we hit "- Personal" line
        if line.strip().startswith('- Personal'):
            break
        filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def generate_prompt(content):
    """
    Generate the prompt for annual review analysis of Readwise work.

    Args:
        content (str): The content to analyze

    Returns:
        str: The complete prompt ready to be used in any AI system
    """
    prompt = f"""Based on these daily journal entries from my time working at Readwise, create a comprehensive summary of my work for my annual review. This should capture both major projects and smaller contributions to give a complete picture of my year.

Please organize the summary into these sections:

## Major Projects
- List the significant projects, features, or initiatives I worked on
- For each project, provide a short description (1-2 sentences) of what it was and my role
- Include both completed projects and ongoing major work
- Focus on projects that took significant time/effort or had notable impact

## Other Stuff
- List smaller tasks, improvements, fixes, and contributions I made
- Include routine but important work that supports the team/product
- Bug fixes, code reviews, documentation, process improvements, etc.
- One-off tasks, experiments, investigations, and smaller features
- Meetings, planning sessions, and collaborative work that moved things forward

For both sections:
- Be comprehensive - include all meaningful work, not just the most impressive items
- Use clear, concise language suitable for a performance review
- Organize items roughly by importance/impact within each section
- Include context about technologies, tools, or areas of the product when relevant

This is for my annual review, so I want to show the full scope of my contributions throughout the year, both big and small.

Journal entries:
{content}"""

    return prompt


def main(start_date=None):
    """
    Main function to generate Readwise work annual review prompt.

    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format.
                                    Defaults to "2024-10-01"
    """
    # Get content from all Readwise work period notes
    content = get_readwise_work_notes(start_date=start_date)

    if not content:
        print("No notes found for the specified date range")
        return

    # Get date range for the header
    start_date, end_date = get_readwise_work_dates(start_date)

    # Generate the prompt
    prompt = generate_prompt(content)

    # Save prompt to file for manual AI processing
    output_file = f"ignore/readwise_work_prompt_{start_date}_to_{end_date}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Readwise Work Annual Review Prompt ({start_date} to {end_date})\n")
        f.write("# Copy the content below and paste it into your preferred AI system\n\n")
        f.write(prompt)

    # Print results
    print(f"\nReadwise Work Annual Review Prompt Generated ({start_date} to {end_date}):")
    print("=" * 70)
    print("Prompt saved to file for manual AI processing.")
    print(f"File: {output_file}")
    print(f"\nThe prompt contains {len(prompt.split())} words and {len(prompt)} characters.")
    print("\nYou can now copy the content from the file and paste it into:")
    print("- ChatGPT")
    print("- Claude")
    print("- Gemini")
    print("- Or any other AI system")
    print("\nThe prompt is optimized for generating comprehensive annual review content about your Readwise work.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate annual review prompt from Readwise work journal entries"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date in YYYY-MM-DD format (default: 2024-10-01)"
    )
    args = parser.parse_args()
    main(start_date=args.start_date)
