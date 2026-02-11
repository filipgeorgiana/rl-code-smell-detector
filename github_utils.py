import requests
import os
from datetime import datetime
from typing import Optional

def get_repo_age(repo_url: str) -> Optional[int]:
    try:
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 2:
            print(f"Invalid URL format: {repo_url}")
            return None

        owner = parts[-2]
        repo = parts[-1].replace('.git', '')

        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"

        headers = {}
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            headers['Authorization'] = f'token {github_token}'
            print("Using GitHub token for authentication")
        else:
            print("Warning: No GITHUB_TOKEN found. Rate limit is 60 requests/hour.")

        # Get the most recent commit
        response = requests.get(api_url, params={'per_page': 1}, headers=headers, timeout=10)

        if response.status_code == 403:
            print(f"GitHub API rate limit exceeded. Headers: {response.headers.get('X-RateLimit-Remaining')}")
            return None
        elif response.status_code != 200:
            print(f"GitHub API error: Status {response.status_code}, Response: {response.text}")
            return None

        commits = response.json()
        if not commits or not isinstance(commits, list):
            print(f"No commits found or unexpected response format: {commits}")
            return None

        # Get the most recent commit date
        last_commit_date_str = commits[0]['commit']['committer']['date']
        last_commit_date = datetime.fromisoformat(last_commit_date_str.replace('Z', '+00:00'))

        # Get the first commit using pagination from the Link header
        link_header = response.headers.get('Link', '')
        first_commit_date = None

        if 'rel="last"' in link_header:
            for part in link_header.split(','):
                if 'rel="last"' in part:
                    last_page_url = part.split(';')[0].strip().strip('<>')
                    last_page_response = requests.get(last_page_url, headers=headers, timeout=10)
                    if last_page_response.status_code == 200:
                        last_page_commits = last_page_response.json()
                        if last_page_commits and isinstance(last_page_commits, list):
                            first_commit_date_str = last_page_commits[-1]['commit']['committer']['date']
                            first_commit_date = datetime.fromisoformat(first_commit_date_str.replace('Z', '+00:00'))
                    break
        else:
            first_commit_date = last_commit_date

        if first_commit_date is None:
            print("Could not determine the first commit date.")
            return None

        repo_age_days = (last_commit_date - first_commit_date).days

        print(f"Repository: {owner}/{repo}")
        print(f"First commit date: {first_commit_date}")
        print(f"Last commit date: {last_commit_date}")
        print(f"Repository age (days): {repo_age_days}")

        return repo_age_days

    except KeyError as e:
        print(f"Error parsing commit data - missing key: {e}")
        return None
    except Exception as e:
        print(f"Error fetching repository age: {e}")
        import traceback
        traceback.print_exc()
        return None