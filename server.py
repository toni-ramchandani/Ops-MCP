#!/usr/bin/env python3
"""
GitHub MCP Server - Python implementation
A Model Context Protocol server that provides GitHub API functionality
"""

import os
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from github import Github, GithubException
from github.Repository import Repository
from github.Issue import Issue
from github.PullRequest import PullRequest
from mcp.server.fastmcp import FastMCP

# Local helpers for secure filesystem operations
from fs_utils import (
    resolve_and_validate,
    read_file_text,
    list_directory as fs_list_directory,
)

# Load environment variables
load_dotenv()

# Create MCP server
mcp = FastMCP("GitHub MCP Server")

# ---------------------------------------------------------------------------
# Filesystem MCP – Resources & Tools
# ---------------------------------------------------------------------------

# Resource: expose file content as readable data via MCP. Supports deep paths.

@mcp.resource("file://{file_path}")
def get_file(file_path: str) -> str:
    """Return text content of a file within allowed directories.

    If the file exceeds the inline limit, the output will be truncated with a
    notice. Binary data is decoded using UTF-8 with replacement of undecodable
    bytes, ensuring the response is always valid UTF-8 for LLM consumption.
    """
    try:
        return read_file_text(file_path)
    except Exception as exc:
        return f"Error reading file: {exc}"


# Tool: read_file – wrapper that returns JSON structure

@mcp.tool()
def read_file(path: str) -> Dict[str, Any]:
    """Read text content of *path* and return it inside a JSON envelope."""
    try:
        content = read_file_text(path)
        return {"path": path, "content": content}
    except Exception as exc:
        return {"error": str(exc)}


# Tool: write_file – create or overwrite a file

@mcp.tool()
def write_file(path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
    """Write *content* to *path*.

    If *overwrite* is False and the file exists, the operation will fail.
    """
    try:
        p = resolve_and_validate(path)
        if p.exists() and not overwrite:
            return {"error": "File exists and overwrite is False"}
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"path": str(p), "bytes_written": len(content)}
    except Exception as exc:
        return {"error": str(exc)}


# Tool: list_directory – list entries in a directory

@mcp.tool()
def list_directory(path: str = ".") -> Dict[str, Any]:
    """Return names and types of entries in *path*."""
    try:
        entries = fs_list_directory(path)
        return {"path": path, "entries": entries}
    except Exception as exc:
        return {"error": str(exc)}


def get_github_client() -> Github:
    """Get authenticated GitHub client"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return Github(token)

# Resources - Data that can be read by LLMs
@mcp.resource("github://repos/{owner}/{repo}")
def get_repository(owner: str, repo: str) -> str:
    """Get repository information"""
    try:
        github = get_github_client()
        repository = github.get_repo(f"{owner}/{repo}")
        
        repo_data = {
            "name": repository.name,
            "full_name": repository.full_name,
            "description": repository.description,
            "private": repository.private,
            "html_url": repository.html_url,
            "clone_url": repository.clone_url,
            "language": repository.language,
            "stargazers_count": repository.stargazers_count,
            "forks_count": repository.forks_count,
            "open_issues_count": repository.open_issues_count,
            "default_branch": repository.default_branch,
            "created_at": repository.created_at.isoformat(),
            "updated_at": repository.updated_at.isoformat(),
            "pushed_at": repository.pushed_at.isoformat() if repository.pushed_at else None,
        }
        
        return json.dumps(repo_data, indent=2)
    except GithubException as e:
        return f"Error accessing repository: {e.data.get('message', str(e))}"

@mcp.resource("github://repos/{owner}/{repo}/issues")
def get_repository_issues(owner: str, repo: str) -> str:
    """Get repository issues"""
    try:
        github = get_github_client()
        repository = github.get_repo(f"{owner}/{repo}")
        issues = repository.get_issues(state="open")
        
        issues_data = []
        for issue in issues[:10]:  # Limit to first 10 issues
            issues_data.append({
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "user": issue.user.login,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "html_url": issue.html_url,
                "body": issue.body[:500] if issue.body else None  # Truncate body
            })
        
        return json.dumps(issues_data, indent=2)
    except GithubException as e:
        return f"Error accessing issues: {e.data.get('message', str(e))}"

# Tools - Actions that can be performed by LLMs
@mcp.tool()
def search_repositories(query: str, sort: str = "stars", order: str = "desc") -> Dict[str, Any]:
    """Search for repositories on GitHub"""
    try:
        github = get_github_client()
        repos = github.search_repositories(query=query, sort=sort, order=order)
        
        results = []
        for repo in repos[:10]:  # Limit to first 10 results
            results.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "html_url": repo.html_url,
                "stargazers_count": repo.stargazers_count,
                "language": repo.language,
                "updated_at": repo.updated_at.isoformat()
            })
        
        return {
            "total_count": repos.totalCount,
            "repositories": results
        }
    except GithubException as e:
        return {"error": f"Search failed: {e.data.get('message', str(e))}"}

@mcp.tool()
def get_repository_info(owner: str, repo: str) -> Dict[str, Any]:
    """Get detailed information about a repository"""
    try:
        github = get_github_client()
        repository = github.get_repo(f"{owner}/{repo}")
        
        return {
            "name": repository.name,
            "full_name": repository.full_name,
            "description": repository.description,
            "private": repository.private,
            "html_url": repository.html_url,
            "clone_url": repository.clone_url,
            "ssh_url": repository.ssh_url,
            "language": repository.language,
            "stargazers_count": repository.stargazers_count,
            "watchers_count": repository.watchers_count,
            "forks_count": repository.forks_count,
            "open_issues_count": repository.open_issues_count,
            "default_branch": repository.default_branch,
            "created_at": repository.created_at.isoformat(),
            "updated_at": repository.updated_at.isoformat(),
            "pushed_at": repository.pushed_at.isoformat() if repository.pushed_at else None,
            "size": repository.size,
            "topics": repository.get_topics(),
            "license": repository.license.name if repository.license else None,
        }
    except GithubException as e:
        return {"error": f"Repository not found: {e.data.get('message', str(e))}"}

@mcp.tool()
def list_repository_issues(owner: str, repo: str, state: str = "open", labels: Optional[str] = None) -> Dict[str, Any]:
    """List issues for a repository"""
    try:
        github = get_github_client()
        repository = github.get_repo(f"{owner}/{repo}")
        
        kwargs = {"state": state}
        if labels:
            kwargs["labels"] = labels.split(",")
        
        issues = repository.get_issues(**kwargs)
        
        issues_data = []
        for issue in issues[:20]:  # Limit to first 20 issues
            issues_data.append({
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "user": issue.user.login,
                "assignees": [assignee.login for assignee in issue.assignees],
                "labels": [label.name for label in issue.labels],
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "html_url": issue.html_url,
                "body": issue.body[:1000] if issue.body else None  # Truncate body
            })
        
        return {
            "repository": f"{owner}/{repo}",
            "issues": issues_data
        }
    except GithubException as e:
        return {"error": f"Failed to list issues: {e.data.get('message', str(e))}"}

@mcp.tool()
def get_issue_details(owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """Get detailed information about a specific issue"""
    try:
        github = get_github_client()
        repository = github.get_repo(f"{owner}/{repo}")
        issue = repository.get_issue(issue_number)
        
        return {
            "number": issue.number,
            "title": issue.title,
            "state": issue.state,
            "user": issue.user.login,
            "assignees": [assignee.login for assignee in issue.assignees],
            "labels": [label.name for label in issue.labels],
            "milestone": issue.milestone.title if issue.milestone else None,
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            "html_url": issue.html_url,
            "body": issue.body,
            "comments": issue.comments,
            "repository": f"{owner}/{repo}"
        }
    except GithubException as e:
        return {"error": f"Issue not found: {e.data.get('message', str(e))}"}

@mcp.tool()
def list_pull_requests(owner: str, repo: str, state: str = "open") -> Dict[str, Any]:
    """List pull requests for a repository"""
    try:
        github = get_github_client()
        repository = github.get_repo(f"{owner}/{repo}")
        pulls = repository.get_pulls(state=state)
        
        pulls_data = []
        for pr in pulls[:20]:  # Limit to first 20 PRs
            pulls_data.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "user": pr.user.login,
                "head": {
                    "ref": pr.head.ref,
                    "sha": pr.head.sha
                },
                "base": {
                    "ref": pr.base.ref,
                    "sha": pr.base.sha
                },
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "html_url": pr.html_url,
                "mergeable": pr.mergeable,
                "draft": pr.draft
            })
        
        return {
            "repository": f"{owner}/{repo}",
            "pull_requests": pulls_data
        }
    except GithubException as e:
        return {"error": f"Failed to list pull requests: {e.data.get('message', str(e))}"}

@mcp.tool()
def get_user_info(username: str) -> Dict[str, Any]:
    """Get information about a GitHub user"""
    try:
        github = get_github_client()
        user = github.get_user(username)
        
        return {
            "login": user.login,
            "name": user.name,
            "email": user.email,
            "bio": user.bio,
            "company": user.company,
            "location": user.location,
            "blog": user.blog,
            "html_url": user.html_url,
            "public_repos": user.public_repos,
            "public_gists": user.public_gists,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "type": user.type
        }
    except GithubException as e:
        return {"error": f"User not found: {e.data.get('message', str(e))}"}

if __name__ == "__main__":
    # Run the server
    mcp.run() 