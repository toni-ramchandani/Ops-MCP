from __future__ import annotations

"""Async utilities for a shared Playwright browser instance.

Uses Playwright's **async API** so it can safely run inside the event loop
created by FastMCP / FastAPI.
"""

import base64
import secrets
from typing import Dict

from playwright.async_api import async_playwright, Playwright, Browser, Page

_playwright: Playwright | None = None
_browser: Browser | None = None
_context = None  # type: ignore
_pages: Dict[str, Page] = {}


async def _ensure_browser() -> None:
    """Launch a headless Chromium browser if it hasn't been started yet."""
    global _playwright, _browser, _context
    if _browser is None:
        _playwright = await async_playwright().start()
        # Launch with optimized settings for faster startup
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        _context = await _browser.new_context(
            # Disable images and CSS for faster loading during testing
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )


def _generate_page_id() -> str:
    return secrets.token_hex(8)


async def new_page(url: str | None = None) -> str:
    """Create a new page, optionally navigate, return its ID."""
    await _ensure_browser()
    page = await _context.new_page()  # type: ignore[name-defined]
    if url:
        await page.goto(url)
    pid = _generate_page_id()
    _pages[pid] = page
    return pid


async def get_page(pid: str) -> Page:
    page = _pages.get(pid)
    if not page:
        raise KeyError(f"Unknown page_id '{pid}'.")
    return page


async def close_page(pid: str) -> None:
    page = _pages.pop(pid, None)
    if page:
        await page.close()


async def page_screenshot_base64(pid: str, **kwargs) -> str:
    page = await get_page(pid)
    buf = await page.screenshot(**kwargs)
    encoded = base64.b64encode(buf).decode("ascii")
    return f"data:image/png;base64,{encoded}" 