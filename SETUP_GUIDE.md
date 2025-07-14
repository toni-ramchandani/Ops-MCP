# How We Built This GitHub MCP Server

A simple step-by-step guide to creating an MCP server in Python.

## Step 1: Project Setup

Created `pyproject.toml` with MCP dependencies:
```toml
[project]
name = "github-mcp-server"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.11.0",
    "PyGithub>=2.6.1", 
    "python-dotenv>=1.0.0",
]
```

## Step 2: Basic Server Structure

Created `server.py` with FastMCP:
```python
from mcp.server.fastmcp import FastMCP
from github import Github
import os

# Create MCP server
mcp = FastMCP("GitHub MCP Server")

# GitHub client helper
def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    return Github(token)
```

## Step 3: Add Resources (Data Access)

Resources provide data to LLMs:
```python
@mcp.resource("github://repos/{owner}/{repo}")
def get_repository(owner: str, repo: str) -> str:
    github = get_github_client()
    repo = github.get_repo(f"{owner}/{repo}")
    return json.dumps(repo_data)
```

## Step 4: Add Tools (Actions)

Tools let LLMs perform actions:
```python
@mcp.tool()
def search_repositories(query: str) -> Dict[str, Any]:
    github = get_github_client()
    repos = github.search_repositories(query)
    return {"repositories": results}
```

## Step 5: Run the Server

Add at the end of `server.py`:
```python
if __name__ == "__main__":
    mcp.run()
```

## Step 6: Environment Setup

Create `.env` file:
```
GITHUB_TOKEN=your_token_here
```

## Step 7: Test It

```bash
# Install dependencies
pip install "mcp[cli]>=1.11.0" "PyGithub>=2.6.1" "python-dotenv>=1.0.0"

# Test with MCP Inspector
uv run mcp dev server.py

# Or run directly
python server.py
```

## That's It!

You now have a working MCP server that can:
- Provide GitHub data through resources
- Execute GitHub actions through tools
- Work with any MCP-compatible client (like Claude Desktop)

The key concepts:
- **FastMCP**: The framework that handles MCP protocol
- **Resources**: Data endpoints (like `@mcp.resource`)
- **Tools**: Action endpoints (like `@mcp.tool`)
- **Environment**: Secure token management 