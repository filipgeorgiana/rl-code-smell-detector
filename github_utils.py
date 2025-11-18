import requests
from datetime import datetime, timezone
from typing import Optional


def get_repo_age(repo_url: str) -> Optional[int]:
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

        # Get the first (oldest) commit
        # We need to get the total count first, then fetch the last page
        first_commit_response = requests.get(api_url, params={'per_page': 1, 'page': 1})

        if first_commit_response.status_code != 200:
            return None

        # Check if there's a Link header to get the last page
        link_header = first_commit_response.headers.get('Link', '')
        if 'last' in link_header:
            # Extract the last page number from the Link header
            import re
            last_page_match = re.search(r'page=(\d+)>; rel="last"', link_header)
            if last_page_match:
                last_page = int(last_page_match.group(1))
                first_commit_response = requests.get(api_url, params={'per_page': 1, 'page': last_page})

                if first_commit_response.status_code != 200:
                    return None

        first_commits = first_commit_response.json()
        if not first_commits:
            return None

        first_commit_date_str = first_commits[0]['commit']['committer']['date']
        first_commit_date = datetime.fromisoformat(first_commit_date_str.replace('Z', '+00:00'))

        age_days = (last_commit_date - first_commit_date).days

        return age_days

    except Exception as e:
        print(f"Error fetching repository age: {e}")
        return None