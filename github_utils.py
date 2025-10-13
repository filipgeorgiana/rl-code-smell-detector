import requests
from datetime import datetime, timezone
from typing import Optional

# name is not great but I didn't have better ideas..

def get_repo_last_update(repo_url: str) -> Optional[int]:
    try:
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 2:
            return None

        owner = parts[-2]
        repo = parts[-1].replace('.git', '')

        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        response = requests.get(api_url, params={'per_page': 1})

        if response.status_code != 200:
            return None

        commits = response.json()
        if not commits:
            return None

        last_commit_date_str = commits[0]['commit']['committer']['date']
        last_commit_date = datetime.fromisoformat(last_commit_date_str.replace('Z', '+00:00'))

        now = datetime.now(timezone.utc)
        age_days = (now - last_commit_date).days

        return age_days

    except Exception as e:
        print(f"Error fetching repository age: {e}")
        return None