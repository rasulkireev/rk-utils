import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def parse_year(date_str):
    if not date_str:
        return None
    try:
        if date_str.endswith("Z"):
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).year
        return datetime.fromisoformat(date_str).year
    except ValueError:
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").year
        except ValueError:
            return None


def fetch_titles_for_year(db_path, year):
    print(f"Loading chat titles from {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT title, created_at FROM chats WHERE title IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    print(f"Loaded {len(rows)} rows. Filtering for {year}...")

    seen = set()
    titles = []
    for title, created_at in rows:
        if not title:
            continue
        if parse_year(created_at) != year:
            continue
        cleaned = title.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        titles.append(cleaned)

    return titles


def summarize_titles_with_openai(
    titles, year, model, confirm_send=True, prompt_out_path=None
):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    client = OpenAI(api_key=api_key)

    titles_block = "\n".join(f"- {title}" for title in titles)
    prompt = f"""You are helping summarize a year of interests.

Given the chat titles from {year}, identify major interest categories and describe them.

Requirements:
- Output 5-8 major categories.
- For each category, include 2-5 concise bullet points.

Output format:

## Category
- <bullet>
- <bullet>

Here are the conversation titles:
{titles_block}"""

    titles_chars = len(titles_block)
    prompt_chars = len(prompt)
    titles_words = len(titles_block.split())
    prompt_words = len(prompt.split())
    estimated_prompt_tokens = max(1, int(prompt_chars / 4))

    print(f"Preparing request for {model}...")
    print(f"- Titles: {len(titles)}")
    print(f"- Titles chars: {titles_chars:,}")
    print(f"- Titles words: {titles_words:,}")
    print(f"- Prompt chars: {prompt_chars:,}")
    print(f"- Prompt words: {prompt_words:,}")
    print(f"- Est. prompt tokens: {estimated_prompt_tokens:,}")
    if prompt_out_path:
        prompt_path = Path(prompt_out_path).expanduser()
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt, encoding="utf-8")
        print(f"Prompt written to {prompt_path}")
        return ""

    if confirm_send:
        answer = input("Send request now? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Request cancelled.")
            return ""

    print(f"Sending to {model} for summary...")

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=500,
    )
    print("Summary received.")
    return (response.output_text or "").strip()


def main():
    parser = argparse.ArgumentParser(
        description="Summarize yearly interests from TypingMind chat titles."
    )
    parser.add_argument("year", type=int, help="Year to summarize (e.g., 2024)")
    parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path(__file__).parent / "chats.db"),
        help="Path to chats.db (default: src/typingmind/chats.db)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5.2",
        help="OpenAI model name (default: gpt-5.2)",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Send request without interactive confirmation",
    )
    parser.add_argument(
        "--prompt-out",
        type=str,
        help="Write the prompt to a file and skip the API call",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path).expanduser()
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return

    titles = fetch_titles_for_year(db_path, args.year)
    if not titles:
        print(f"No chat titles found for {args.year}")
        return
    print(f"Found {len(titles)} unique titles for {args.year}.")

    try:
        summary = summarize_titles_with_openai(
            titles,
            args.year,
            args.model,
            confirm_send=not args.no_confirm,
            prompt_out_path=args.prompt_out,
        )
    except ValueError as e:
        print(f"Error: {e}")
        return

    if not summary:
        return

    print(f"\nInterests summary for {args.year}:")
    print("=" * 50)
    print(summary)


if __name__ == "__main__":
    # poetry run python src/typingmind/summarize_yearly_interests.py 2025
    main()
