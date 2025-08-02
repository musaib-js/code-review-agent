import requests


def fetch_pr_code_diff(repo_url: str, pr_number: int, github_token: str = None) -> str:
    owner_repo = repo_url.rstrip("/").split("github.com/")[-1]
    url = f"https://patch-diff.githubusercontent.com/raw/{owner_repo}/pull/{pr_number}.diff"
    headers = {}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        
    print(f"Fetching PR diff from: {url} with token: {github_token if github_token else 'Not Provided'}")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text
