"""Async HTTP + headless-browser fetchers with automatic fallback.

Refactored port of va_fastapiclient/.../webscraper/fetchers.py.
Only difference: uses VxThinkingLLM's logger instead of app.core.logger.

Strategy:
    1. Try httpx (fast, lightweight) first.
    2. If httpx returns < MIN_BODY_BYTES, raises, or hits 403/429,
       fall back to Playwright (if installed).
    3. Playwright is optional — if not installed, the failure
       surfaces to the caller as an empty body.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, Tuple

logger = logging.getLogger("VxThinkingLLM.web.fetchers")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    # Drop "br" (brotli) — httpx only decodes gzip/deflate without the optional brotli pkg.
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
}

MIN_BODY_BYTES = 256
HTTPX_TIMEOUT = 20.0
PLAYWRIGHT_TIMEOUT_MS = 30_000


async def httpx_fetch(url: str, timeout: float = HTTPX_TIMEOUT) -> Tuple[str, int, str]:
    """Fetch URL with httpx. Returns (html, status_code, final_url)."""
    import httpx

    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=timeout,
        http2=False,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text, resp.status_code, str(resp.url)


def playwright_available() -> bool:
    try:
        from playwright.async_api import async_playwright  # noqa: F401
        return True
    except ImportError:
        return False


async def playwright_fetch(
    url: str,
    wait_selector: Optional[str] = None,
    viewport: Tuple[int, int] = (1280, 800),
    take_screenshot: bool = False,
) -> Tuple[str, int, str, Optional[bytes]]:
    """Fetch URL via Playwright Chromium headless."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    width, height = viewport
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            ctx = await browser.new_context(
                user_agent=DEFAULT_HEADERS["User-Agent"],
                locale="en-US",
                viewport={"width": width, "height": height},
            )
            page = await ctx.new_page()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=8_000)
                except Exception:
                    pass
            try:
                await page.wait_for_load_state("networkidle", timeout=8_000)
            except Exception:
                pass

            html = await page.content()
            status_code = response.status if response else 0
            final_url = page.url

            screenshot = await page.screenshot(full_page=False) if take_screenshot else None
            return html, status_code, final_url, screenshot
        finally:
            await browser.close()


async def fetch_with_fallback(
    url: str,
    use_playwright: bool = False,
    wait_selector: Optional[str] = None,
    take_screenshot: bool = False,
) -> dict:
    """Smart fetcher: try httpx, fall back to Playwright when needed."""
    result = {
        "html": "",
        "fetcher": "httpx",
        "status_code": None,
        "final_url": url,
        "load_time_ms": None,
        "screenshot_bytes": None,
        "errors": [],
    }
    start = time.perf_counter()

    if not use_playwright:
        try:
            html, status, final_url = await httpx_fetch(url)
            result.update(
                html=html,
                status_code=status,
                final_url=final_url,
                load_time_ms=int((time.perf_counter() - start) * 1000),
            )
            if html and len(html) >= MIN_BODY_BYTES and not take_screenshot:
                return result
            if not html or len(html) < MIN_BODY_BYTES:
                result["errors"].append("httpx returned near-empty body, escalating to Playwright")
                logger.info("httpx returned near-empty body for %s", url)
        except Exception as exc:
            result["errors"].append(f"httpx failed: {exc}")
            logger.info("httpx fetch failed for %s: %s", url, exc)

    if not playwright_available():
        result["errors"].append("Playwright not installed; cannot fall back")
        return result

    try:
        html, status, final_url, screenshot = await playwright_fetch(
            url,
            wait_selector=wait_selector,
            take_screenshot=take_screenshot,
        )
        result.update(
            html=html,
            fetcher="playwright",
            status_code=status,
            final_url=final_url,
            load_time_ms=int((time.perf_counter() - start) * 1000),
            screenshot_bytes=screenshot,
        )
    except Exception as exc:
        result["errors"].append(f"Playwright failed: {exc}")
        logger.warning("Playwright fetch failed for %s: %s", url, exc)

    return result


def fetch_with_fallback_sync(
    url: str,
    use_playwright: bool = False,
    wait_selector: Optional[str] = None,
    take_screenshot: bool = False,
) -> dict:
    """Synchronous wrapper around `fetch_with_fallback`."""
    coro = fetch_with_fallback(url, use_playwright, wait_selector, take_screenshot)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)
