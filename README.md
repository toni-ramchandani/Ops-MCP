# GitHub MCP Server (Python)

A Python implementation of the GitHub MCP Server using the Model Context Protocol (MCP). This server provides GitHub API functionality through MCP resources and tools, allowing LLMs to interact with GitHub repositories, issues, pull requests, and users.

## Features

This MCP server replicates the functionality of the [official GitHub MCP server](https://github.com/github/github-mcp-server) and provides:

### Resources (Data Access)
- **Repository Information**: Get detailed repository data
- **Issues**: Access repository issues and their details

### Tools (Actions)
- **Search Repositories**: Search for repositories on GitHub
- **Repository Info**: Get detailed information about a repository
- **List Issues**: List issues for a repository with filtering
- **Issue Details**: Get detailed information about a specific issue
- **List Pull Requests**: List pull requests for a repository
- **User Information**: Get information about GitHub users

### Additional Capabilities

#### File System Access
- Securely **read**, **write**, and **list** files/directories inside paths defined by the `FS_ALLOWED_DIRS` environment variable.

#### Browser Automation (Playwright)
- Headless Chromium automation: open pages, click elements, fill forms, capture screenshots, and extract text.
- **Web Search (Tavily)**: Real-time search results from the public web using the Tavily API.

## Prerequisites

- Python 3.10 or higher
- A GitHub Personal Access Token

## Installation

1. **Clone or create the project**:
   ```bash
   # If you have the files, just navigate to the directory
   cd github-mcp-server
   ```

2. **Install dependencies**:
   ```bash
   # Using pip
   pip install "mcp[cli]>=1.11.0" "PyGithub>=2.6.1" "python-dotenv>=1.0.0" "playwright>=1.44.0" "requests>=2.31.0"
   
   # Or using uv (recommended)
   uv add "mcp[cli]>=1.11.0" "PyGithub>=2.6.1" "python-dotenv>=1.0.0" "playwright>=1.44.0" "requests>=2.31.0"
   ```

3. **Install browser binaries (one-time)**:
```bash
python -m playwright install
```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```bash
   GITHUB_TOKEN=your_github_personal_access_token_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

   Or set the environment variable directly:
   ```bash
   export GITHUB_TOKEN=your_github_personal_access_token_here
   export TAVILY_API_KEY=your_tavily_api_key_here
   ```

## Getting a GitHub Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select the scopes you need:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories)
   - `read:user` (for user information)
4. Copy the generated token and add it to your `.env` file

## Usage

### Development Mode (Testing)

Test your server with the MCP Inspector:

```bash
# Using uv
uv run mcp dev server.py

# Using python directly
python server.py
```

### Claude Desktop Integration

Install the server in Claude Desktop:

```bash
# Basic installation
uv run mcp install server.py

# With custom name
uv run mcp install server.py --name "GitHub MCP Server"

# With environment variables
uv run mcp install server.py -f .env
```

### Direct Execution

Run the server directly:

```bash
python server.py
```

## Filesystem Configuration

Set `FS_ALLOWED_DIRS` to a list of absolute directories the server may access (colon-separated on macOS/Linux, semicolon-separated on Windows). Example:

```bash
export FS_ALLOWED_DIRS="/home/user/projects:/tmp"
```

If unset, the current working directory is used.

## Available Resources

### Repository Information
- **URI**: `github://repos/{owner}/{repo}`
- **Description**: Get detailed repository information
- **Example**: `github://repos/microsoft/vscode`

### Repository Issues
- **URI**: `github://repos/{owner}/{repo}/issues`
- **Description**: Get open issues for a repository
- **Example**: `github://repos/microsoft/vscode/issues`

### File Content
- **URI**: `file://{file_path}`
- **Description**: Return UTF-8 text content of a file within the allowed directories.
- **Example**: `file:///home/user/projects/README.md`

## Available Tools

### search_repositories
Search for repositories on GitHub.

**Parameters**:
- `query` (string): Search query
- `sort` (string, optional): Sort by "stars", "forks", "updated" (default: "stars")
- `order` (string, optional): "asc" or "desc" (default: "desc")

### get_repository_info
Get detailed information about a repository.

**Parameters**:
- `owner` (string): Repository owner
- `repo` (string): Repository name

### list_repository_issues
List issues for a repository.

**Parameters**:
- `owner` (string): Repository owner
- `repo` (string): Repository name
- `state` (string, optional): "open", "closed", or "all" (default: "open")
- `labels` (string, optional): Comma-separated list of labels

### get_issue_details
Get detailed information about a specific issue.

**Parameters**:
- `owner` (string): Repository owner
- `repo` (string): Repository name
- `issue_number` (integer): Issue number

### list_pull_requests
List pull requests for a repository.

**Parameters**:
- `owner` (string): Repository owner
- `repo` (string): Repository name
- `state` (string, optional): "open", "closed", or "all" (default: "open")

### get_user_info
Get information about a GitHub user.

**Parameters**:
- `username` (string): GitHub username

### read_file
Read text content of a file.

**Parameters**:
- `path` (string): Path to the file (must be inside allowed dirs)

### write_file
Write content to a file.

**Parameters**:
- `path` (string): Target file path
- `content` (string): Text to write
- `overwrite` (bool, optional): Defaults to `true`

### list_directory
List entries in a directory.

**Parameters**:
- `path` (string, optional): Directory to list (default `"."`)

### browser_open_page
Open a URL in a new headless browser tab.

**Parameters**:
- `url` (string): Page URL
- `wait_until` (string, optional): `"load"`, `"domcontentloaded"`, or `"networkidle"` (default `"load"`)
- `timeout_ms` (int, optional): Navigation timeout in ms (default `10000`)

### browser_close_page
Close an open browser tab.

**Parameters**:
- `page_id` (string): The identifier returned by `browser_open_page`

### browser_click
Click a DOM element.

**Parameters**:
- `page_id` (string)
- `selector` (string): CSS selector
- `timeout_ms` (int, optional)

### browser_fill
Fill or type text into an element.

**Parameters**:
- `page_id` (string)
- `selector` (string)
- `text` (string)
- `timeout_ms` (int, optional)
- `clear` (bool, optional): Clear existing content first (default `true`)

### browser_get_text
Retrieve the innerText of an element.

**Parameters**:
- `page_id` (string)
- `selector` (string)
- `timeout_ms` (int, optional)

### browser_screenshot
Capture a PNG screenshot as a base64 data URL.

**Parameters**:
- `page_id` (string)
- `full_page` (bool, optional): Capture full page (default `false`)

### web_search
Search the public web using Tavily.

**Parameters**:
- `query` (string)
- `max_results` (int, optional, 1-20)
- `include_domains` (string, optional)
- `exclude_domains` (string, optional)
- `search_depth` (string, optional): "basic" or "advanced" (default "advanced")

Returns Tavily response JSON with result items, metadata, etc.

## Example Usage

Once the server is running and connected to an LLM client, you can:

1. **Search for repositories**:
   ```
   Search for Python web frameworks
   ```

2. **Get repository information**:
   ```
   Get information about the microsoft/vscode repository
   ```

3. **List issues**:
   ```
   List open issues for the microsoft/vscode repository
   ```

4. **Get user information**:
   ```
   Get information about the GitHub user "octocat"
   ```

## Error Handling

The server includes comprehensive error handling:
- Invalid GitHub tokens
- Repository not found
- Rate limiting
- Network errors
- API errors

All errors are returned in a structured format with descriptive messages.

## Rate Limiting

Be aware of GitHub's rate limits:
- 5,000 requests per hour for authenticated requests
- 60 requests per hour for unauthenticated requests

The server will return appropriate error messages when rate limits are exceeded.

## Security

- Never commit your GitHub token to version control
- Use environment variables or `.env` files for sensitive data
- Consider using GitHub Apps for production deployments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. 