"""Website crawler using httpx + BeautifulSoup, with Playwright fallback."""

import logging
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import config

logger = logging.getLogger(__name__)

PRIORITY_PATHS = ["/", "/ueber-uns", "/about", "/about-us", "/kontakt", "/contact",
                  "/leistungen", "/services", "/team", "/impressum"]

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}


async def _fetch_with_httpx(url: str, timeout: int) -> str | None:
    """Try fetching with httpx. Returns HTML or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=BROWSER_HEADERS)
            if response.status_code == 403:
                logger.info(f"httpx got 403 for {url}, will try Playwright")
                return None
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.info(f"httpx failed for {url}: {e}, will try Playwright")
        return None


def _fetch_with_playwright(url: str, timeout: int) -> str | None:
    """Fallback: fetch with Playwright (non-headless) for bot-protected sites."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not installed, cannot use browser fallback")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            ctx = browser.new_context(
                user_agent=BROWSER_HEADERS["User-Agent"],
                locale="de-DE",
                viewport={"width": 1920, "height": 1080},
            )
            page = ctx.new_page()
            page.add_init_script(
                'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            )
            page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            # Wait a bit for JS-rendered content
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()

            if "Access Denied" in html and len(html) < 1000:
                logger.warning(f"Playwright also got Access Denied for {url}")
                return None
            return html
    except Exception as e:
        logger.error(f"Playwright failed for {url}: {e}")
        return None


async def crawl_url(url: str) -> dict:
    """Crawl a single URL and extract text content.

    Tries httpx first, falls back to Playwright for bot-protected sites.
    Returns dict with keys: url, title, text, links.
    """
    timeout = config.crawler.timeout_seconds

    # Try httpx first (fast)
    html = await _fetch_with_httpx(url, timeout)

    # Fallback to Playwright for protected sites
    if html is None:
        import asyncio
        html = await asyncio.to_thread(_fetch_with_playwright, url, timeout)

    if html is None:
        return {"url": url, "title": "", "text": "", "links": [],
                "error": "Website blockiert automatisierte Zugriffe"}

    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    text = soup.get_text(separator="\n", strip=True)
    # Collapse multiple newlines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    # Truncate very long pages
    if len(text) > 15000:
        text = text[:15000] + "\n...[abgeschnitten]"

    # Extract internal links
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base, href)
        if full_url.startswith(base) and full_url not in links:
            links.append(full_url)

    return {"url": url, "title": title, "text": text, "links": links[:20]}


async def crawl_website(base_url: str) -> list[dict]:
    """Crawl a website starting from the base URL, prioritizing important pages.

    Returns list of page dicts.
    """
    max_pages = config.crawler.max_pages
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    # Start with priority paths
    urls_to_crawl = [urljoin(base, path) for path in PRIORITY_PATHS]
    # Add the original URL if not already in the list
    if base_url not in urls_to_crawl:
        urls_to_crawl.insert(0, base_url)

    crawled = []
    seen = set()

    for url in urls_to_crawl:
        if len(crawled) >= max_pages:
            break
        if url in seen:
            continue
        seen.add(url)

        result = await crawl_url(url)
        if result.get("text") and not result.get("error"):
            crawled.append(result)

    return crawled
