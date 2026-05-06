import requests
import os
import re
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from typing import Optional

def _parse_owner_repo(repo_url: str):
    parts = repo_url.rstrip('/').split('/')
    if len(parts) < 2:
        return None, None
    owner = parts[-2]
    repo = parts[-1].replace('.git', '')
    return owner, repo


def _get_headers():
    headers = {}
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'
        print("Using GitHub token for authentication")
    else:
        print("Warning: No GITHUB_TOKEN found. Rate limit is 60 requests/hour.")
    return headers


def _api_get(url, headers, params=None):
    response = requests.get(url, params=params, headers=headers, timeout=10)
    if response.status_code == 403:
        print(f"GitHub API rate limit exceeded. Headers: {response.headers.get('X-RateLimit-Remaining')}")
        return None
    elif response.status_code != 200:
        print(f"GitHub API error: Status {response.status_code}, Response: {response.text}")
        return None
    return response


def _get_contributor_count(owner, repo, headers):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    response = _api_get(url, headers, params={'per_page': 1, 'anon': 'false'})
    if response is None:
        return None

    link_header = response.headers.get('Link', '')
    if 'rel="last"' in link_header:
        for part in link_header.split(','):
            if 'rel="last"' in part:
                last_page_url = part.split(';')[0].strip().strip('<>')
                match = re.search(r'[?&]page=(\d+)', last_page_url)
                if match:
                    return int(match.group(1))
        return None
    else:
        # Only one page of results
        contributors = response.json()
        if isinstance(contributors, list):
            return len(contributors)
        return None


def get_repo_metadata(repo_url: str) -> Optional[dict]:
    try:
        owner, repo = _parse_owner_repo(repo_url)
        if owner is None:
            print(f"Invalid URL format: {repo_url}")
            return None

        headers = _get_headers()

        # Fetch repo info (stars, topics, size, created_at) in one call
        repo_response = _api_get(f"https://api.github.com/repos/{owner}/{repo}", headers)
        stars = None
        topics = None
        size_kb = None
        if repo_response is not None:
            repo_data = repo_response.json()
            stars = repo_data.get('stargazers_count')
            topics = repo_data.get('topics', [])
            size_kb = repo_data.get('size')

        # Fetch contributor count
        contributors = _get_contributor_count(owner, repo, headers)

        # Compute repo age from first commit date -
        age_months = None
        commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        response = _api_get(commits_url, headers, params={'per_page': 1})
        if response is not None:
            commits = response.json()
            if commits and isinstance(commits, list):
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
                                    first_commit_date_str = last_page_commits[-1]['commit']['author']['date']
                                    first_commit_date = datetime.fromisoformat(first_commit_date_str.replace('Z', '+00:00'))
                            break
                else:
                    first_commit_date_str = commits[0]['commit']['author']['date']
                    first_commit_date = datetime.fromisoformat(first_commit_date_str.replace('Z', '+00:00'))

                if first_commit_date is not None:
                    now = datetime.now(timezone.utc)
                    delta = relativedelta(now, first_commit_date)
                    age_months = delta.years * 12 + delta.months

        metadata = {
            'age_months': age_months,
            'stars': stars,
            'topics': topics,
            'size_kb': size_kb,
            'contributors': contributors,
        }

        print(f"Repository: {owner}/{repo}")
        print(f"Age (months): {age_months}")
        print(f"Stars: {stars}")
        print(f"Topics: {topics}")
        print(f"Size (KB): {size_kb}")
        print(f"Contributors: {contributors}")

        return metadata

    except KeyError as e:
        print(f"Error parsing repository data - missing key: {e}")
        return None
    except Exception as e:
        print(f"Error fetching repository metadata: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_repo_age(repo_url: str) -> Optional[int]:
    metadata = get_repo_metadata(repo_url)
    if metadata is None:
        return None
    return metadata.get('age_months')
