import os
import glob
from pathlib import Path
from datetime import datetime, date


def get_readwise_work_dates():
    """
    Get the date range from October 1, 2023 to today

    Returns:
        tuple: (start_date, end_date) in YYYY-MM-DD format
    """
    start_date = "2023-10-01"
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")
    return start_date, end_date


def get_readwise_work_notes(notes_dir="~/Obsidian/notes/recurring/daily/"):
    """
    Retrieve content from all notes from October 1, 2023 onwards.

    Args:
        notes_dir (str): Directory path containing the notes

    Returns:
        str: Concatenated content of all relevant notes
    """
    notes_dir = os.path.expanduser(notes_dir)
    start_date, end_date = get_readwise_work_dates()

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
                date = Path(file).stem
                all_content.append(f"Date: {date}\n{content}\n---\n")
        except Exception as e:
            print(f"Error reading file {file}: {e}")

    return "\n".join(all_content)


def generate_prompt(content):
    """
    Generate the prompt for resume-focused analysis of Readwise work.

    Args:
        content (str): The content to analyze

    Returns:
        str: The complete prompt ready to be used in any AI system
    """
    prompt = f"""Based on these daily journal entries from my time working at Readwise, create a concise, resume-ready summary of my key accomplishments and contributions. This should be professional, impactful, and highlight my most significant work.

Please organize the summary into these sections:

## Key Accomplishments & Impact
- List 5-7 major achievements with quantifiable results where possible
- Focus on projects that demonstrate technical skills, leadership, or business impact
- Use action verbs and specific outcomes

## Technical Contributions
- Major features, systems, or improvements I built/led
- Technologies and frameworks I worked with
- Any architectural decisions or technical innovations

## Leadership & Collaboration
- Team initiatives I led or contributed to significantly
- Cross-functional work and stakeholder management
- Mentoring or knowledge sharing activities

## Skills Demonstrated
- Technical skills evidenced by the work described
- Soft skills like problem-solving, communication, project management

Keep each bullet point concise (1-2 lines max) and focus on the most impressive, career-advancing work. Write in a professional tone suitable for a resume or LinkedIn profile. Prioritize accomplishments that would be most valuable to future employers.

Do not include routine tasks, meetings, or day-to-day work unless they led to significant outcomes. Focus on what makes me stand out as a candidate.

Journal entries:
{content}"""

    return prompt


def main():
    # Get content from all Readwise work period notes
    content = get_readwise_work_notes()

    if not content:
        print("No notes found for the specified date range")
        return

    # Get date range for the header
    start_date, end_date = get_readwise_work_dates()

    # Generate the prompt
    prompt = generate_prompt(content)

    # Save prompt to file for manual AI processing
    output_file = "readwise_work_prompt.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Readwise Work Analysis Prompt ({start_date} to {end_date})\n")
        f.write("# Copy the content below and paste it into your preferred AI system\n\n")
        f.write(prompt)

    # Print results
    print(f"\nReadwise Work Analysis Prompt Generated ({start_date} to {end_date}):")
    print("=" * 70)
    print("Prompt saved to file for manual AI processing.")
    print(f"File: {output_file}")
    print(f"\nThe prompt contains {len(prompt.split())} words and {len(prompt)} characters.")
    print("\nYou can now copy the content from the file and paste it into:")
    print("- ChatGPT")
    print("- Claude")
    print("- Gemini")
    print("- Or any other AI system")
    print("\nThe prompt is optimized for generating resume-ready content about your Readwise work.")


if __name__ == "__main__":
    main()
