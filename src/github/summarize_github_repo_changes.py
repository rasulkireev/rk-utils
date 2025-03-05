import os
import anthropic
from datetime import datetime, timedelta
from github import Github
import json
from typing import List, Dict
from pathlib import Path
import time
from dotenv import load_dotenv

from src.github.helpers import ensure_cache_directory, generate_master_summary, handle_rate_limit

# Load environment variables from .env file
load_dotenv()

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
