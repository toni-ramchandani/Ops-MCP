import os

from github import Github

def get_github_client() -> Github:
    """Return an authenticated GitHub client using runtime configuration."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not configured.")
    return Github(token)
