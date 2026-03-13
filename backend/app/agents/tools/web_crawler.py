"""Website crawler using httpx + BeautifulSoup."""

import logging
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import config

logger = logging.getLogger(__name__)

PRIORITY_PATHS = ["/", "/ueber-uns", "/about", "/about-us", "/kontakt", "/contact",
                  "/leistungen", "/services", "/team", "/impressum"]


async def crawl_url(url: str) -> dict:
    """Crawl a single URL and extract text content.

    Returns dict with keys: url, title, text, links.
    """
    timeout = config.crawler.timeout_seconds
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "WerbesystemBot/1.0"})
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to crawl {url}: {e}")
        return {"url": url, "title": "", "text": "", "links": [], "error": str(e)}

    soup = BeautifulSoup(response.text, "html.parser")

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
