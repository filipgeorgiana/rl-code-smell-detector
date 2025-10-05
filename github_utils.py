import requests
from datetime import datetime, timezone
from typing import Optional


def get_repo_age_days(repo_url: str) -> Optional[int]:
    """
    Calculate the age of a GitHub repository in days based on the last commit time.

    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/username/repo)

    Returns:
        Repository age in days, or None if the request fails
    """
    try:
        # Extract owner and repo name from URL
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 2:
            return None

        owner = parts[-2]
        repo = parts[-1].replace('.git', '')

        # Call GitHub API to get the latest commit
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        response = requests.get(api_url, params={'per_page': 1})

        if response.status_code != 200:
            return None

        commits = response.json()
        if not commits:
            return None

        # Get the last commit date
        last_commit_date_str = commits[0]['commit']['committer']['date']
        last_commit_date = datetime.fromisoformat(last_commit_date_str.replace('Z', '+00:00'))

        # Calculate age in days
        now = datetime.now(timezone.utc)
        age_days = (now - last_commit_date).days

        return age_days

    except Exception as e:
        print(f"Error fetching repository age: {e}")
        return None