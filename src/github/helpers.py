from typing import Dict
import anthropic
import os
from pathlib import Path
import json
import datetime
import time
from github import Github

def handle_rate_limit(g: Github):
    """Handle GitHub API rate limit by waiting if necessary."""
    rate_limit = g.get_rate_limit()
    remaining = rate_limit.core.remaining

    print(f"Current API calls remaining: {remaining}")

    if remaining == 0:
        reset_timestamp = rate_limit.core.reset.timestamp()
        sleep_time = reset_timestamp - time.time() + 1  # Add 1 second buffer
        if sleep_time > 0:
            reset_time = datetime.fromtimestamp(reset_timestamp).strftime('%H:%M:%S')
            print(f"\nGitHub API rate limit reached!")
            print(f"Waiting for {sleep_time:.2f} seconds (until {reset_time})...")

            # Print a progress dot every 30 seconds
            dots_to_print = int(sleep_time / 30)
            for _ in range(dots_to_print):
                time.sleep(30)
                print(".", end="", flush=True)

            time_remaining = sleep_time % 30
            if time_remaining > 0:
                time.sleep(time_remaining)

            print("\nRate limit reset, resuming operations...")


def ensure_cache_directory() -> Path:
    """Ensure the cache directory exists and return its path."""
    current_dir = Path.cwd()  # Get current working directory
    cache_dir = current_dir / 'caches'
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def analyze_commit(client: anthropic.Client, commit, repo_url: str) -> dict:
    """Analyze a single commit using Claude."""
    # Extract owner and repo name from URL for commit link
    _, _, _, owner, repo_name = repo_url.rstrip('/').split('/')
    commit_url = f"https://github.com/{owner}/{repo_name}/commit/{commit.sha}"

    # Initialize GitHub client for getting commit details
    g = Github(os.getenv('GITHUB_TOKEN'))
    handle_rate_limit(g)

    try:
        commit_info = {
            'sha': commit.sha,
            'message': commit.commit.message,
            'author': {
                'name': commit.commit.author.name,
                'email': commit.commit.author.email
            },
            'date': commit.commit.author.date.isoformat(),
            'url': commit_url,
            'files': [
                {
                    'filename': file.filename,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes
                }
                for file in commit.files
            ]
        }
    except Exception as e:
        if "rate limit" in str(e).lower():
            handle_rate_limit(g)
            # Retry after handling rate limit
            return analyze_commit(client, commit, repo_url)
        raise e

    prompt = f"""
    Analyze this GitHub commit and provide a concise summary of the changes.
    Focus on what was changed and why. Be specific but brief.

    Commit data:
    {json.dumps(commit_info, indent=2)}
    """

    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=1000,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return {
        "summary": message.content[0].text,
        "url": commit_url,
        "date": commit_info['date'],
        "author": commit_info['author'],
        "sha": commit.sha
    }


def generate_master_summary(client: anthropic.Client, summaries: Dict[str, dict], start_date: datetime, repo_url: str) -> str:
    """Generate a master summary from individual commit summaries."""
    if not summaries:
        return "No commits found for the specified time period."

    # Extract owner and repo name from URL
    _, _, _, owner, repo_name = repo_url.rstrip('/').split('/')

    # Prepare a more structured summary of commits for Claude
    formatted_summaries = []
    for sha, data in summaries.items():
        formatted_summaries.append({
            "summary": data["summary"],
            "url": data["url"],
            "date": data["date"],
            "author": data["author"]["name"],
            "sha": data["sha"]
        })

    prompt = f"""
    Review these {len(summaries)} commit summaries for {start_date.strftime('%B %Y')} and provide a comprehensive overview of all changes.
    Focus on the main themes, features, bug fixes, and overall development progress.

    Repository: {repo_url}
    Time period: {start_date.strftime('%B %Y')}
    Number of commits: {len(summaries)}

    Commit summaries:
    {json.dumps(formatted_summaries, indent=2)}

    Please provide the summary in a structured format with sections for:
    1. Overview
    2. Key Changes and Features (include commit URLs and author names in parentheses for each point)
    3. Development Patterns and Contributors
    4. Recommendations (if any)

    Example format for changes:
    - Implemented user authentication system (by John Doe - https://github.com/owner/repo/commit/abc123)
    """

    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=1000,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text
