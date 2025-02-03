import os
import anthropic
from datetime import datetime, timedelta
from github import Github
import json
from typing import List, Dict
from pathlib import Path
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def ensure_cache_directory() -> Path:
    """Ensure the cache directory exists and return its path."""
    current_dir = Path.cwd()  # Get current working directory
    cache_dir = current_dir / 'caches'
    cache_dir.mkdir(exist_ok=True)
    return cache_dir

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

def get_existing_commits_for_month(summaries_file: Path, month_start: datetime, month_end: datetime) -> Dict[str, dict]:
    """Get existing commit summaries for the specified month."""
    if not summaries_file.exists():
        return {}

    try:
        with open(summaries_file, 'r') as f:
            all_summaries = json.load(f)

        print(f"\nChecking {len(all_summaries)} total summaries for period: "
              f"{month_start.strftime('%Y-%m-%d')} to {month_end.strftime('%Y-%m-%d')}")

        # Filter summaries for the specified month
        month_summaries = {}
        for sha, summary in all_summaries.items():
            try:
                commit_date = summary.get('date')
                if commit_date:
                    # Print some debug info for the first few entries
                    if len(month_summaries) < 3:
                        print(f"Processing commit date: {commit_date}")

                    # Handle both full ISO format and date-only format
                    if 'T' in commit_date:
                        commit_datetime = datetime.fromisoformat(commit_date.split('T')[0])
                    else:
                        commit_datetime = datetime.fromisoformat(commit_date)

                    if month_start <= commit_datetime < month_end:
                        month_summaries[sha] = summary
            except (ValueError, AttributeError) as e:
                print(f"Warning: Could not process date for commit {sha[:7]}: {e}")
                continue

        print(f"Found {len(month_summaries)} commits for the specified month")
        return month_summaries
    except Exception as e:
        print(f"Error reading existing summaries: {e}")
        return {}

def get_month_commits(repo_url: str, date: datetime) -> tuple[List, str]:
    """Get all commits for a specific month from a GitHub repository."""
    # Calculate start and end of the month
    start_date = date.replace(day=1)
    if date.month == 12:
        end_date = date.replace(year=date.year + 1, month=1, day=1)
    else:
        end_date = date.replace(month=date.month + 1, day=1)

    print(f"\nFetching commits for {start_date.strftime('%B %Y')}...")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    # Extract owner and repo name from URL
    _, _, _, owner, repo_name = repo_url.rstrip('/').split('/')
    print(f"Repository: {owner}/{repo_name}")

    # Initialize GitHub client
    print("Initializing GitHub client...")
    g = Github(os.getenv('GITHUB_TOKEN'))

    try:
        print("Accessing repository...")
        repo = g.get_repo(f"{owner}/{repo_name}")

        # Get commits for the specified month
        print("Starting to fetch commits...")
        commits = []
        commit_pages = repo.get_commits(since=start_date, until=end_date)

        # Get total count if available
        try:
            total_count = commit_pages.totalCount
            print(f"Total commits to fetch: {total_count}")
        except Exception:
            print("Unable to get total commit count, proceeding anyway...")

        for i, commit in enumerate(commit_pages, 1):
            if i % 10 == 0:  # Print progress every 10 commits
                print(f"Fetched {i} commits so far...")
            handle_rate_limit(g)
            commits.append(commit)

        print(f"Successfully fetched {len(commits)} commits")
        return commits, repo_name

    except Exception as e:
        if "rate limit" in str(e).lower():
            print("Hit rate limit, waiting to reset...")
            handle_rate_limit(g)
            # Retry after handling rate limit
            return get_month_commits(repo_url, date)
        print(f"Error during commit fetching: {str(e)}")
        raise e

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


if __name__ == "__main__":
    # Verify environment variables
    required_env_vars = ['GITHUB_TOKEN', 'ANTHROPIC_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please add them to your .env file")
        exit(1)

    # Configuration
    repo_url = "https://github.com/django/django"

    # Get the date for analysis
    try:
        date_input = input("Enter a date within the month you want to analyze (YYYY-MM-DD): ")
        analysis_date = datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD")
        exit(1)

    try:
        # Calculate month range
        month_start = analysis_date.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)

        # Create output file paths
        cache_dir = ensure_cache_directory()
        summaries_file = cache_dir / f"django_commit_summaries.json"  # Using explicit name instead of repo_name
        master_file = cache_dir / f"django_{analysis_date.strftime('%Y_%m')}_master_summary.txt"

        # Check existing summaries first
        existing_month_summaries = get_existing_commits_for_month(summaries_file, month_start, month_end)
        print(f"Found {len(existing_month_summaries)} existing summaries for {month_start.strftime('%B %Y')}")

        # Ask if user wants to fetch new commits
        response = input("Do you want to fetch new commits from GitHub? (y/n): ")

        if response.lower() == 'y':
            # Get new commits
            commits, repo_name = get_month_commits(repo_url, analysis_date)
            print(f"Found {len(commits)} commits")

            # Load all existing summaries
            existing_summaries = {}
            if summaries_file.exists():
                with open(summaries_file, 'r') as f:
                    existing_summaries = json.load(f)

            # Initialize Anthropic client
            client = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))

            # Analyze new commits
            summaries = existing_summaries.copy()
            for i, commit in enumerate(commits, 1):
                if commit.sha in summaries:
                    print(f"Skipping commit {i}/{len(commits)} (already analyzed)")
                    continue

                print(f"Analyzing commit {i}/{len(commits)} ({commit.sha[:7]})")
                try:
                    result = analyze_commit(client, commit, repo_url)
                    summaries[commit.sha] = result

                    # Save after each successful analysis
                    with open(summaries_file, 'w') as f:
                        json.dump(summaries, f, indent=2)
                    print(f"Saved summary to {summaries_file}")

                except Exception as e:
                    print(f"Error analyzing commit {commit.sha[:7]}: {str(e)}")
                    continue

            # Update existing_month_summaries with new analyses
            existing_month_summaries = get_existing_commits_for_month(summaries_file, month_start, month_end)

        # Generate master summary only if we have commits for the month
        if existing_month_summaries:
            print(f"\nGenerating master summary for {len(existing_month_summaries)} commits...")
            client = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))
            master_summary = generate_master_summary(client, existing_month_summaries, month_start, repo_url)

            with open(master_file, 'w') as f:
                f.write(master_summary)

            print(f"\nMaster summary saved to {master_file}")
            print("\nAnalysis complete!")
        else:
            print(f"\nNo commits found for {month_start.strftime('%B %Y')}. Cannot generate master summary.")

    except Exception as e:
        print(f"Error: {str(e)}")
