import os
import anthropic
from datetime import datetime, timedelta
from github import Github
import json
from typing import List, Dict
from pathlib import Path
import time
from dotenv import load_dotenv

from src.github.helpers import analyze_commit, ensure_cache_directory, generate_master_summary, handle_rate_limit

load_dotenv()


def get_date_range(days_back: int) -> tuple[datetime, datetime]:
    """Calculate the date range based on number of days back from today."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date

def get_period_commits(repo_url: str, start_date: datetime, end_date: datetime) -> tuple[List, str]:
    """Get all commits for a specific period from a GitHub repository."""
    print(f"\nFetching commits from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
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

        # Get commits for the specified period
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
            return get_period_commits(repo_url, start_date, end_date)
        print(f"Error during commit fetching: {str(e)}")
        raise e

def get_existing_commits_for_period(summaries_file: Path, start_date: datetime, end_date: datetime) -> Dict[str, dict]:
    """Get existing commit summaries for the specified period."""
    if not summaries_file.exists():
        return {}

    try:
        with open(summaries_file, 'r') as f:
            all_summaries = json.load(f)

        print(f"\nChecking {len(all_summaries)} total summaries for period: "
              f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        # Filter summaries for the specified period
        period_summaries = {}
        for sha, summary in all_summaries.items():
            try:
                commit_date = summary.get('date')
                if commit_date:
                    # Handle both full ISO format and date-only format
                    if 'T' in commit_date:
                        commit_datetime = datetime.fromisoformat(commit_date.split('T')[0])
                    else:
                        commit_datetime = datetime.fromisoformat(commit_date)

                    if start_date <= commit_datetime <= end_date:
                        period_summaries[sha] = summary
            except (ValueError, AttributeError) as e:
                print(f"Warning: Could not process date for commit {sha[:7]}: {e}")
                continue

        print(f"Found {len(period_summaries)} commits for the specified period")
        return period_summaries
    except Exception as e:
        print(f"Error reading existing summaries: {e}")
        return {}

if __name__ == "__main__":
    # Verify environment variables
    required_env_vars = ['GITHUB_TOKEN', 'ANTHROPIC_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please add them to your .env file")
        exit(1)

    # Configuration
    repo_url = "https://github.com/django/django"  # You can modify this or make it an input

    # Get the number of days back
    try:
        days_back = int(input("Enter the number of days back to analyze: "))
        if days_back <= 0:
            raise ValueError("Number of days must be positive")
    except ValueError as e:
        print(f"Invalid input: {e}")
        exit(1)

    try:
        # Calculate date range
        start_date, end_date = get_date_range(days_back)
        print(f"\nAnalyzing commits from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        # Create output file paths
        cache_dir = ensure_cache_directory()
        summaries_file = cache_dir / "django_commit_summaries.json"
        master_file = cache_dir / f"django_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}_summary.txt"

        # Check existing summaries first
        existing_period_summaries = get_existing_commits_for_period(summaries_file, start_date, end_date)
        print(f"Found {len(existing_period_summaries)} existing summaries for the period")

        # Ask if user wants to fetch new commits
        response = input("Do you want to fetch new commits from GitHub? (y/n): ")

        if response.lower() == 'y':
            # Get new commits
            commits, repo_name = get_period_commits(repo_url, start_date, end_date)
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

                # Add retry mechanism for overloaded errors
                max_retries = 5
                retry_count = 0
                retry_delay = 10  # Initial delay in seconds

                while retry_count <= max_retries:
                    try:
                        result = analyze_commit(client, commit, repo_url)
                        summaries[commit.sha] = result

                        # Save after each successful analysis
                        with open(summaries_file, 'w') as f:
                            json.dump(summaries, f, indent=2)
                        print(f"Saved summary to {summaries_file}")
                        break  # Success, exit retry loop

                    except Exception as e:
                        error_str = str(e)
                        if "overloaded_error" in error_str and retry_count < max_retries:
                            retry_count += 1
                            actual_delay = retry_delay * retry_count
                            print(f"Anthropic API overloaded. Retrying in {actual_delay} seconds... (Attempt {retry_count}/{max_retries})")
                            time.sleep(actual_delay)
                        else:
                            print(f"Error analyzing commit {commit.sha[:7]}: {error_str}")
                            break  # Exit retry loop for other errors or if max retries reached

                if retry_count > max_retries:
                    print(f"Maximum retries exceeded for commit {commit.sha[:7]}, skipping.")
                    continue

            # Update existing_period_summaries with new analyses
            existing_period_summaries = get_existing_commits_for_period(summaries_file, start_date, end_date)

        # Generate master summary only if we have commits for the period
        if existing_period_summaries:
            print(f"\nGenerating master summary for {len(existing_period_summaries)} commits...")
            client = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))
            master_summary = generate_master_summary(client, existing_period_summaries, start_date, repo_url)

            with open(master_file, 'w') as f:
                f.write(master_summary)

            print(f"\nMaster summary saved to {master_file}")
            print("\nAnalysis complete!")
        else:
            print(f"\nNo commits found for the specified period. Cannot generate master summary.")

    except Exception as e:
        print(f"Error: {str(e)}")
