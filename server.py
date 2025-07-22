#!/usr/bin/env python3
"""
GitHub MCP Server - Python implementation
A Model Context Protocol server that provides GitHub API functionality
"""

import os
import json
from typing import Optional, Dict, Any, List
import requests  # new dependency for Tavily API
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

import os
import json
from typing import Optional, Dict, Any, List
from browser_utils import (
    new_page,
    get_page,
    close_page,
    page_screenshot_base64,
)
from playwright.async_api import TimeoutError as PWTimeoutError

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

# ---------------------------------------------------------------------------
# Browser Automation MCP – Tools powered by Playwright (async)
# ---------------------------------------------------------------------------

@mcp.tool()
async def browser_open_page(url: str, wait_until: str = "domcontentloaded", timeout_ms: int = 15000) -> Dict[str, Any]:
    """Open *url* in a new headless Chromium tab and return the page ID.
    
    Args:
        url: The URL to navigate to
        wait_until: When to consider navigation successful ('load', 'domcontentloaded', 'networkidle')
        timeout_ms: Maximum time to wait in milliseconds (default: 15 seconds)
    """
    try:
        # Create page first
        pid = await new_page()
        page = await get_page(pid)
        
        # Use very conservative timeout to stay well under MCP limits
        actual_timeout = min(timeout_ms, 12000)  # Max 12 seconds to stay under MCP timeout
        
        # Use domcontentloaded by default - faster than waiting for all resources
        await page.goto(url, wait_until=wait_until, timeout=actual_timeout)
        
        # Get basic page info
        title = await page.title()
        current_url = page.url
        
        return {
            "page_id": pid, 
            "url": current_url, 
            "title": title,
            "status": "success",
            "wait_condition": wait_until
        }
    except PWTimeoutError as exc:
        # Page was created but navigation timed out
        return {
            "page_id": pid if 'pid' in locals() else None,
            "url": url,
            "error": f"Navigation timeout after {actual_timeout}ms. Use browser_get_page_info to check if page loaded.",
            "status": "timeout",
            "suggestion": "Try 'domcontentloaded' wait condition for faster loading"
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "status": "error"
        }


@mcp.tool()
async def browser_close_page(page_id: str) -> Dict[str, Any]:
    try:
        await close_page(page_id)
        return {"status": "closed", "page_id": page_id}
    except KeyError:
        return {"error": f"Unknown page_id '{page_id}'"}


@mcp.tool()
async def browser_get_page_info(page_id: str) -> Dict[str, Any]:
    """Get current information about a browser page (URL, title, ready state)."""
    try:
        page = await get_page(page_id)
        title = await page.title()
        url = page.url
        
        # Check if page is still loading
        ready_state = await page.evaluate("document.readyState")
        
        return {
            "page_id": page_id,
            "url": url,
            "title": title,
            "ready_state": ready_state,
            "status": "success"
        }
    except Exception as exc:
        return {"error": str(exc), "status": "error"}


@mcp.tool()
async def browser_health_check() -> Dict[str, Any]:
    """Quick health check to verify browser automation is working."""
    try:
        # This should be very fast
        pid = await new_page()
        page = await get_page(pid)
        
        # Navigate to a very simple, fast-loading page
        await page.goto("data:text/html,<h1>Browser Test</h1>", timeout=5000)
        title = await page.title()
        
        # Clean up
        await close_page(pid)
        
        return {
            "status": "healthy",
            "message": "Browser automation is working correctly",
            "test_title": title
        }
    except Exception as exc:
        return {
            "status": "error", 
            "error": str(exc),
            "message": "Browser automation is not working"
        }


@mcp.tool()
async def browser_click(page_id: str, selector: str, timeout_ms: int = 10000) -> Dict[str, Any]:
    try:
        page = await get_page(page_id)
        await page.click(selector, timeout=timeout_ms)
        return {"clicked": selector, "page_id": page_id}
    except KeyError:
        return {"error": f"Unknown page_id '{page_id}'"}
    except PWTimeoutError:
        return {"error": f"Timeout waiting for selector '{selector}'"}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
async def browser_fill(page_id: str, selector: str, text: str, timeout_ms: int = 10000, clear: bool = True) -> Dict[str, Any]:
    try:
        page = await get_page(page_id)
        if clear:
            await page.fill(selector, text, timeout=timeout_ms)
        else:
            await page.type(selector, text, timeout=timeout_ms)
        return {"filled": selector, "text": text, "page_id": page_id}
    except KeyError:
        return {"error": f"Unknown page_id '{page_id}'"}
    except PWTimeoutError:
        return {"error": f"Timeout waiting for selector '{selector}'"}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
async def browser_get_text(page_id: str, selector: str, timeout_ms: int = 10000) -> Dict[str, Any]:
    try:
        page = await get_page(page_id)
        await page.wait_for_selector(selector, timeout=timeout_ms)
        text = await page.inner_text(selector)
        return {"text": text, "selector": selector, "page_id": page_id}
    except KeyError:
        return {"error": f"Unknown page_id '{page_id}'"}
    except PWTimeoutError:
        return {"error": f"Timeout waiting for selector '{selector}'"}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
async def browser_screenshot(page_id: str, full_page: bool = False) -> Dict[str, Any]:
    try:
        data_url = await page_screenshot_base64(page_id, full_page=full_page)
        return {"page_id": page_id, "screenshot": data_url}
    except KeyError:
        return {"error": f"Unknown page_id '{page_id}'"}
    except Exception as exc:
        return {"error": str(exc)}

# ---------------------------------------------------------------------------
# (End of browser tools)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Web Search – Tavily API
# ---------------------------------------------------------------------------

def get_tavily_api_key() -> str:
    """Return Tavily API key from env or raise ValueError."""
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise ValueError("TAVILY_API_KEY environment variable is required")
    return key

@mcp.tool()
def web_search(query: str, max_results: int = 10, include_domains: str | None = None,
               exclude_domains: str | None = None, search_depth: str = "advanced") -> Dict[str, Any]:
    """Search the web using Tavily and return JSON results.

    Parameters:
    - query: Search query string.
    - max_results: Maximum number of results (1-20).
    - include_domains / exclude_domains: Comma-separated domain filters.
    - search_depth: "basic" or "advanced".
    """
    try:
        api_key = get_tavily_api_key()
        url = "https://api.tavily.com/search"
        payload: Dict[str, Any] = {
            "api_key": api_key,
            "query": query,
            "max_results": max(1, min(max_results, 20)),
            "search_depth": search_depth,
        }
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code != 200:
            return {"error": f"Tavily API error {resp.status_code}: {resp.text}"}
        data = resp.json()
        return data
    except Exception as exc:
        return {"error": str(exc)}

# ---------------------------------------------------------------------------
# MCP Prompts – Pre-built conversation templates
# ---------------------------------------------------------------------------

@mcp.prompt()
def analyze_repository(owner: str, repo: str) -> List[Dict[str, str]]:
    """Analyze a GitHub repository comprehensively including code, issues, and activity."""
    return [
        {
            "role": "system",
            "content": """You are an expert software engineer and technical analyst. You will analyze a GitHub repository comprehensively to provide insights about its:

1. **Technical Overview**: Languages, frameworks, architecture patterns
2. **Code Quality**: Structure, documentation, testing practices  
3. **Community Health**: Issue management, contribution patterns, maintenance status
4. **Development Activity**: Recent commits, release patterns, contributor activity
5. **Dependencies**: Key libraries, potential security concerns
6. **Recommendations**: Suggestions for improvement or adoption considerations

Use the available MCP tools to gather information systematically. Start with the repository resource and tools, then examine issues, pull requests, and recent activity."""
        },
        {
            "role": "user", 
            "content": f"Please analyze the GitHub repository {owner}/{repo}. Provide a comprehensive technical analysis covering all the areas mentioned in the system prompt. Use the available tools to gather fresh data about the repository."
        }
    ]

@mcp.prompt()
def debug_issue(owner: str, repo: str, issue_number: int) -> List[Dict[str, str]]:
    """Help debug and analyze a specific GitHub issue with context and suggestions."""
    return [
        {
            "role": "system",
            "content": """You are a skilled software engineer and debugging specialist. You will help analyze and debug a specific GitHub issue by:

1. **Issue Analysis**: Understanding the problem description, reproduction steps, and expected vs actual behavior
2. **Context Gathering**: Examining related code, recent changes, similar issues
3. **Root Cause Investigation**: Identifying potential causes based on the information available
4. **Solution Strategies**: Proposing debugging approaches and potential fixes
5. **Action Plan**: Recommending concrete next steps for resolution

Use the available MCP tools to gather comprehensive information about the issue, repository context, and any related discussions."""
        },
        {
            "role": "user",
            "content": f"I need help debugging issue #{issue_number} in {owner}/{repo}. Please analyze the issue thoroughly, gather relevant context from the repository, and provide debugging guidance and potential solutions."
        }
    ]

@mcp.prompt()
def code_review_checklist(language: str = "general") -> List[Dict[str, str]]:
    """Generate a comprehensive code review checklist for a specific programming language."""
    return [
        {
            "role": "system", 
            "content": f"""You are an expert code reviewer and software engineering mentor. Create a comprehensive code review checklist tailored for {language} development that covers:

**Code Quality & Style**:
- Consistent formatting and naming conventions
- Code clarity and readability
- Proper commenting and documentation

**Functionality & Logic**:
- Correctness of implementation
- Edge case handling
- Error handling and validation

**Performance & Efficiency**:
- Algorithm efficiency
- Resource usage optimization
- Scalability considerations

**Security**:
- Input validation and sanitization
- Authentication and authorization
- Data protection and privacy

**Maintainability**:
- Code organization and structure
- Modularity and reusability
- Testing coverage and quality

**Language-Specific Best Practices**:
- Idioms and patterns specific to {language}
- Framework and library usage
- Platform-specific considerations

Format this as a practical checklist that reviewers can use systematically."""
        },
        {
            "role": "user",
            "content": f"Create a detailed code review checklist for {language} development. Make it comprehensive but practical for daily use by development teams."
        }
    ]

@mcp.prompt()
def research_topic(topic: str, focus_area: str = "general") -> List[Dict[str, str]]:
    """Research a technical topic using web search and provide comprehensive analysis."""
    return [
        {
            "role": "system",
            "content": """You are a technical researcher and analyst. You will research a given topic thoroughly using web search capabilities and provide:

1. **Current State**: Latest developments, trends, and industry adoption
2. **Technical Details**: How it works, key concepts, implementation approaches
3. **Ecosystem**: Related tools, frameworks, libraries, and platforms
4. **Use Cases**: Practical applications, success stories, case studies
5. **Advantages & Challenges**: Benefits, limitations, common pitfalls
6. **Future Outlook**: Emerging trends, roadmap, predictions
7. **Getting Started**: Resources for learning, best practices, recommended tools

Use web search extensively to gather the most current and comprehensive information. Cite sources and provide links where relevant."""
        },
        {
            "role": "user",
            "content": f"Research the topic '{topic}' with focus on '{focus_area}'. Provide a comprehensive technical analysis using current web sources. Include practical insights, current trends, and actionable recommendations."
        }
    ]

@mcp.prompt()
def file_analysis(file_path: str) -> List[Dict[str, str]]:
    """Analyze a source code file for quality, patterns, and improvement suggestions."""
    return [
        {
            "role": "system",
            "content": """You are an expert code analyst and software architect. You will analyze a source code file to provide insights on:

**Code Structure & Organization**:
- Overall architecture and design patterns
- Module/class organization
- Function/method design and cohesion

**Code Quality Assessment**:
- Readability and maintainability
- Adherence to best practices
- Documentation quality

**Potential Issues**:
- Code smells and anti-patterns
- Performance concerns
- Security vulnerabilities

**Improvement Recommendations**:
- Refactoring opportunities
- Design pattern applications
- Testing strategies

**Dependencies & Coupling**:
- External dependencies analysis
- Coupling and cohesion assessment
- Interface design evaluation

Use the file reading capabilities to examine the code and provide specific, actionable feedback."""
        },
        {
            "role": "user",
            "content": f"Please analyze the source code file at '{file_path}'. Provide a comprehensive code quality assessment with specific improvement recommendations."
        }
    ]

@mcp.prompt()
def web_automation_plan(task_description: str, target_url: str = "") -> List[Dict[str, str]]:
    """Create a step-by-step plan for web automation tasks using browser tools."""
    return [
        {
            "role": "system",
            "content": """You are a web automation specialist and QA engineer. You will create detailed automation plans for web-based tasks using browser automation tools. Your plan should include:

**Strategy & Approach**:
- Task breakdown and workflow design
- Risk assessment and error handling
- Data validation and verification steps

**Technical Implementation**:
- Step-by-step browser automation sequence
- CSS selectors and element identification
- Wait conditions and timing considerations

**Quality Assurance**:
- Verification points and assertions
- Error scenarios and recovery actions
- Data integrity checks

**Best Practices**:
- Robust selector strategies
- Performance optimization
- Maintainability considerations

Use the available browser automation tools (open_page, click, fill, get_text, screenshot) to implement the solution."""
        },
        {
            "role": "user",
            "content": f"Create a detailed web automation plan for: '{task_description}'" + (f" on the website: {target_url}" if target_url else "") + ". Provide step-by-step instructions using the available browser automation tools."
        }
    ]

# ---------------------------------------------------------------------------
# (End of MCP Prompts)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Run the server
    mcp.run() 