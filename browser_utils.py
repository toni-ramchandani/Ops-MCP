from __future__ import annotations

"""Utilities for a shared Playwright browser instance and page registry.

This module launches a headless Chromium browser at import time and exposes
helpers to create pages and map them to simple string IDs so that MCP tools
can reference them across calls.

Since the MCP server processes requests sequentially in the same interpreter
process by default, a simple in-memory registry is sufficient. If you scale
out the server, you may want to replace this with a more robust session store.
"""

import base64
import secrets
from typing import Dict, Optional

from playwright.sync_api import Playwright, sync_playwright, Browser, Page

# ---------------------------------------------------------------------------
# Browser lifecycle
# ---------------------------------------------------------------------------

_playwright: Playwright | None = None
_browser: Browser | None = None
_context = None  # type: ignore
_pages: Dict[str, Page] = {}


def _ensure_browser() -> None:
    """Start Playwright and a headless Chromium browser if not already running."""
    global _playwright, _browser, _context
    if _browser is None:
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=True)
        _context = _browser.new_context()


# ---------------------------------------------------------------------------
# Page management helpers
# ---------------------------------------------------------------------------


def _generate_page_id() -> str:
    """Return a cryptographically secure random page identifier."""
    return secrets.token_hex(8)


def new_page(url: str | None = None) -> str:
    """Create a new page, optionally navigate to *url*, and return its ID."""
    _ensure_browser()
    page = _context.new_page()  # type: ignore[name-defined]
    if url:
        page.goto(url)
    pid = _generate_page_id()
    _pages[pid] = page
    return pid


def get_page(pid: str) -> Page:
    """Return the Page object for *pid* or raise KeyError if not found."""
    page = _pages.get(pid)
    if not page:
        raise KeyError(f"Unknown page_id '{pid}'. Did you close it?")
    return page


def close_page(pid: str) -> None:
    """Close the page identified by *pid* and remove it from the registry."""
    page = _pages.pop(pid, None)
    if page:
        page.close()


# ---------------------------------------------------------------------------
# Convenience helpers used by tools
# ---------------------------------------------------------------------------


def page_screenshot_base64(pid: str, **kwargs) -> str:
    """Return a screenshot of the page *pid* encoded as base64 data URL."""
    page = get_page(pid)
    buf = page.screenshot(**kwargs)
    encoded: str = base64.b64encode(buf).decode("ascii")
    return f"data:image/png;base64,{encoded}"


# Note: At process exit we rely on Python's atexit to close the browser. 