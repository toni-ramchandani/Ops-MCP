# github_utils.py
import os
from typing import Any

import httpx

GITHUB_API_BASE = "https://api.github.com"


def get_github_headers() -> dict[str, str]:
    """Build authenticated GitHub API headers from runtime configuration."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not configured.")

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "mcp-developer-assistant",
    }


async def fetch_repository_metadata(owner: str, repo: str) -> dict[str, Any]:
    """Return selected metadata for a GitHub repository."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers=get_github_headers())

    if response.status_code != 200:
        raise ValueError("The requested repository could not be retrieved.")

    repository = response.json()
    return {
        "name": repository["name"],
        "full_name": repository["full_name"],
        "description": repository.get("description"),
        "private": repository["private"],
        "html_url": repository["html_url"],
        "clone_url": repository["clone_url"],
        "language": repository.get("language"),
        "stargazers_count": repository["stargazers_count"],
        "forks_count": repository["forks_count"],
        "open_issues_count": repository["open_issues_count"],
        "default_branch": repository["default_branch"],
        "created_at": repository["created_at"],
        "updated_at": repository["updated_at"],
        "pushed_at": repository.get("pushed_at"),
    }


async def fetch_open_issues(
    owner: str,
    repo: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return a summarized list of open issues for a repository."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
    params = {"state": "open", "per_page": limit}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            url,
            headers=get_github_headers(),
            params=params,
        )

    if response.status_code != 200:
        raise ValueError("The requested issue list could not be retrieved.")

    issues = response.json()
    results: list[dict[str, Any]] = []
    for issue in issues:
        results.append({
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "user": issue["user"]["login"],
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "html_url": issue["html_url"],
            "body": issue.get("body"),
        })
    return results
