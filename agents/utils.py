import requests
import logging

def post_pr_comment(repo_full_name, pr_number, body, commit_id, path, line, github_token):
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "body": body,
        "commit_id": commit_id,
        "path": path,
        "side": "RIGHT",
        "line": line
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 201:
        logging.warning(f"Failed to post comment: {response.status_code} {response.text}")
    else:
        logging.info(f"Comment posted successfully for {path}:{line}")
