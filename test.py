import os

import requests


def fetch_repo_star_info(owner, repo, token):
    url = f'https://api.github.com/repos/{owner}/{repo}'
    headers = {
        'Authorization': f'Token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        repo_data = response.json()
        watchers_count = repo_data.get('subscribers_count', 0)
        forks_count = repo_data.get('forks_count', 0)
        stars_count = repo_data.get('stargazers_count', 0)
        return stars_count

    except requests.exceptions.RequestException as e:
        print(f"Error fetching repository data: {e}")
        return None


github_token = os.environ.get('GH_TOKEN')
repo_owner = 'fmtlib'
repo_name = 'fmt'

star_count = fetch_repo_star_info(repo_owner, repo_name, github_token)

if star_count is not None:
    print(f"The repository {repo_owner}/{repo_name} has {star_count} stars.")
else:
    print("Failed to fetch star information.")
