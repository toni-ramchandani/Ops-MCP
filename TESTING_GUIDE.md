# MCP Server Testing Guide

This document provides a comprehensive step-by-step guide for testing all capabilities of the GitHub MCP Server using MCP Inspector.

## Prerequisites

### 1. Environment Setup
Add these lines to your `.env` file:
```bash
# GitHub API (required for GitHub tools/resources)
GITHUB_TOKEN=your_github_token_here

# Filesystem Access (required for file operations)
FS_ALLOWED_DIRS=C:\Users\ramcton

# Web Search (optional - for web_search tool)
TAVILY_API_KEY=your_tavily_api_key_here
```

### 2. Server Startup
```bash
uv run mcp dev server.py
```

### 3. Open MCP Inspector
Navigate to the MCP Inspector URL provided in the terminal output.

---

## 📁 Filesystem Tools Testing

### 1. `read_file` Tool
**Purpose**: Read text content from a file
- **Parameter**: `path` = `C:\Users\ramcton\Downloads\app.py`
- **Expected Result**: JSON with file content
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 2. `list_directory` Tool
**Purpose**: List files and folders in a directory
- **Parameter**: `path` = `C:\Users\ramcton\Downloads`
- **Expected Result**: Array of file/folder entries with names and types
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 3. `write_file` Tool
**Purpose**: Create or overwrite a file
- **Parameters**: 
  - `path` = `C:\Users\ramcton\Desktop\test_mcp.txt`
  - `content` = `Hello from MCP Server! Testing write functionality.`
  - `overwrite` = `true`
- **Expected Result**: Success message with bytes written
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

---

## 🐙 GitHub Tools Testing

### 4. `search_repositories` Tool
**Purpose**: Search for repositories on GitHub
- **Parameters**:
  - `query` = `python mcp`
  - `sort` = `stars`
  - `order` = `desc`
- **Expected Result**: List of repositories with metadata
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 5. `get_repository_info` Tool
**Purpose**: Get detailed repository information
- **Parameters**:
  - `owner` = `microsoft`
  - `repo` = `vscode`
- **Expected Result**: Complete repository details (stars, forks, language, etc.)
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 6. `list_repository_issues` Tool
**Purpose**: List issues for a repository
- **Parameters**:
  - `owner` = `microsoft`
  - `repo` = `vscode`
  - `state` = `open`
- **Expected Result**: Array of issue objects
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 7. `get_issue_details` Tool
**Purpose**: Get detailed information about a specific issue
- **Parameters**:
  - `owner` = `microsoft`
  - `repo` = `vscode`
  - `issue_number` = `1`
- **Expected Result**: Detailed issue information
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 8. `list_pull_requests` Tool
**Purpose**: List pull requests for a repository
- **Parameters**:
  - `owner` = `microsoft`
  - `repo` = `vscode`
  - `state` = `open`
- **Expected Result**: Array of pull request objects
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 9. `get_user_info` Tool
**Purpose**: Get GitHub user information
- **Parameter**: `username` = `octocat`
- **Expected Result**: User profile information
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

---

## 🔍 Web Search Testing

### 10. `web_search` Tool
**Purpose**: Search the web using Tavily API
- **Parameters**:
  - `query` = `python MCP framework tutorial`
  - `max_results` = `5`
  - `search_depth` = `advanced`
- **Expected Result**: Web search results with URLs and snippets
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

---

## 🌐 Browser Automation Testing

### 11. `browser_health_check` Tool
**Purpose**: Verify browser automation is working
- **Parameters**: None
- **Expected Result**: Status "healthy" with test message
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 12. `browser_open_page` Tool
**Purpose**: Open a webpage in headless browser
- **Parameters**:
  - `url` = `https://example.com`
  - `wait_until` = `domcontentloaded`
  - `timeout_ms` = `15000`
- **Expected Result**: Page ID, URL, and title
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 13. `browser_get_page_info` Tool
**Purpose**: Get current page information
- **Parameter**: `page_id` = _[Use page_id from step 12]_
- **Expected Result**: Page details including ready state
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 14. `browser_click` Tool
**Purpose**: Click an element on the page
- **Parameters**:
  - `page_id` = _[Use page_id from step 12]_
  - `selector` = `h1`
  - `timeout_ms` = `10000`
- **Expected Result**: Success message confirming click
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 15. `browser_get_text` Tool
**Purpose**: Extract text from an element
- **Parameters**:
  - `page_id` = _[Use page_id from step 12]_
  - `selector` = `h1`
  - `timeout_ms` = `10000`
- **Expected Result**: Text content of the element
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 16. `browser_screenshot` Tool
**Purpose**: Take a screenshot of the page
- **Parameters**:
  - `page_id` = _[Use page_id from step 12]_
  - `full_page` = `false`
- **Expected Result**: Base64 encoded screenshot data
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 17. `browser_close_page` Tool
**Purpose**: Close a browser page
- **Parameter**: `page_id` = _[Use page_id from step 12]_
- **Expected Result**: Success confirmation
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

---

## 📄 Resources Testing

### 18. `file://` Resource
**Purpose**: Access file content as a resource
- **URI**: `file://C:\Users\ramcton\Downloads\app.py`
- **Expected Result**: Raw file content
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 19. `github://repos/` Resource
**Purpose**: Access repository data as a resource
- **URI**: `github://repos/microsoft/vscode`
- **Expected Result**: JSON repository information
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 20. `github://repos//issues` Resource
**Purpose**: Access repository issues as a resource
- **URI**: `github://repos/microsoft/vscode/issues`
- **Expected Result**: JSON array of issues
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

---

## 🎯 Prompts Testing

### 21. `analyze_repository` Prompt
**Purpose**: Comprehensive repository analysis template
- **Parameters**:
  - `owner` = `microsoft`
  - `repo` = `vscode`
- **Expected Result**: System and user message array for analysis
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 22. `debug_issue` Prompt
**Purpose**: Issue debugging template
- **Parameters**:
  - `owner` = `microsoft`
  - `repo` = `vscode`
  - `issue_number` = `1`
- **Expected Result**: System and user message array for debugging
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 23. `code_review_checklist` Prompt
**Purpose**: Code review checklist template
- **Parameter**: `language` = `python`
- **Expected Result**: Comprehensive code review checklist
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 24. `research_topic` Prompt
**Purpose**: Research template for technical topics
- **Parameters**:
  - `topic` = `FastAPI`
  - `focus_area` = `microservices`
- **Expected Result**: Research conversation template
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 25. `file_analysis` Prompt
**Purpose**: Source code analysis template
- **Parameter**: `file_path` = `C:\Users\ramcton\Downloads\app.py`
- **Expected Result**: Code analysis conversation template
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

### 26. `web_automation_plan` Prompt
**Purpose**: Web automation planning template
- **Parameters**:
  - `task_description` = `Login to website and extract data`
  - `target_url` = `https://example.com`
- **Expected Result**: Automation planning conversation template
- **Test Status**: ⬜ Pass ⬜ Fail
- **Notes**: _________________

---

## 🚀 Quick Smoke Test (Essential Tests)

For rapid verification, test these critical functions in order:

1. ✅ **browser_health_check** (fastest validation)
2. ✅ **list_directory** with `C:\Users\ramcton`
3. ✅ **search_repositories** with `python mcp`
4. ✅ **browser_open_page** with `https://example.com`
5. ✅ **analyze_repository** prompt with `microsoft/vscode`

## 🔧 Troubleshooting

### Common Issues

1. **"Failed to fetch" on filesystem tools**
   - Solution: Add `FS_ALLOWED_DIRS=C:\Users\ramcton` to `.env`

2. **"MCP error -32001: Request timed out" on browser tools**
   - Solution: Use `browser_health_check` first, try simpler URLs

3. **GitHub API errors**
   - Solution: Verify `GITHUB_TOKEN` in `.env` file

4. **Web search errors**
   - Solution: Add `TAVILY_API_KEY` to `.env` file

### Environment Variables Check
```bash
# Check if environment variables are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('FS_ALLOWED_DIRS:', os.getenv('FS_ALLOWED_DIRS')); print('GITHUB_TOKEN:', 'SET' if os.getenv('GITHUB_TOKEN') else 'NOT SET')"
```

---

## 📊 Testing Summary

**Total Tests**: 26
- **Tools**: 17
- **Resources**: 3  
- **Prompts**: 6

**Completion Status**: ___/26 (___%)

**Date Tested**: _____________
**Tester**: _____________
**Server Version**: _____________

---

## 📝 Notes Section

Use this space for additional observations, issues, or improvements:

```
_________________________________________________________________________
_________________________________________________________________________
_________________________________________________________________________
_________________________________________________________________________
_________________________________________________________________________
``` 