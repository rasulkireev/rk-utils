import os
import glob
import argparse
from pathlib import Path
from datetime import datetime, timedelta

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


def get_last_n_days_date_range(days=14):
    if days < 1:
        raise ValueError("days must be >= 1")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    return start_date, end_date


def get_notes_for_date_range(notes_dir, start_date, end_date):
    notes_dir = os.path.expanduser(notes_dir)
    all_files = glob.glob(os.path.join(notes_dir, "*.md"))
    matched_files = []

    for file in all_files:
        date_str = Path(file).stem
        try:
            file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if start_date <= file_date <= end_date:
            matched_files.append(file)

    matched_files.sort()
    return matched_files


def extract_readwise_bullets(note_content):
    """
    Extract bullet points under the "Readwise" section in the "Log" heading.
    """
    lines = note_content.splitlines()
    in_log_section = False
    in_readwise_section = False
    readwise_items = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            if stripped == "## Log":
                in_log_section = True
                in_readwise_section = False
                continue
            if in_log_section:
                break

        if not in_log_section:
            continue

        if stripped == "- Readwise":
            in_readwise_section = True
            continue

        if in_readwise_section:
            if stripped.startswith("- ") and not line.startswith((" ", "\t")):
                break
            if stripped.startswith(("- ", "* ")):
                item = stripped[2:].strip()
                if item:
                    readwise_items.append(item)

    return readwise_items


def build_readwise_log_string(files):
    chunks = []
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file}: {e}")
            continue

        items = extract_readwise_bullets(content)
        if not items:
            continue

        date = Path(file).stem
        formatted_items = "\n".join(f"- {item}" for item in items)
        chunks.append(f"Date: {date}\n{formatted_items}")

    return "\n\n".join(chunks)


def analyze_with_openai(content, model):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    client = OpenAI(api_key=api_key)

    prompt = f"""You are helping identify the biggest team-shareable win.

From the Readwise work log entries below (last 2 weeks), identify the single biggest win.

Requirements:
- Output 1-3 sentences.
- Be specific and concrete.
- If multiple wins are similar, pick the most impactful.

Entries:
{content}"""

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=300,
    )
    return (response.output_text or "").strip()


def main():
    parser = argparse.ArgumentParser(
        description="Find the biggest Readwise win from the last N days of Obsidian logs."
    )
    parser.add_argument(
        "--notes-dir",
        type=str,
        default="/Users/rasul/Obsidian/notes/recurring/daily/",
        help="Directory containing the daily notes",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Number of days to look back (inclusive of today)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5.2",
        help="OpenAI model name (default: gpt-5.2)",
    )

    args = parser.parse_args()

    start_date, end_date = get_last_n_days_date_range(args.days)
    files = get_notes_for_date_range(args.notes_dir, start_date, end_date)

    if not files:
        print("No notes found in the requested date range")
        return

    readwise_log = build_readwise_log_string(files)
    if not readwise_log:
        print("No Readwise entries found in the requested date range")
        return

    try:
        result = analyze_with_openai(readwise_log, args.model)
    except ValueError as e:
        print(f"Error: {e}")
        return

    print(f"\nBiggest win ({start_date} to {end_date}):")
    print("=" * 50)
    print(result)


if __name__ == "__main__":
    main()
