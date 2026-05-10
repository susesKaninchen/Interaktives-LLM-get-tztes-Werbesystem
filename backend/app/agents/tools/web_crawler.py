"""Website crawler using httpx + BeautifulSoup, with improved stability."""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
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

# Rate limiting configuration
REQUEST_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds

# Cache configuration
CACHE_DIR = Path("./data/crawl_cache")
CACHE_TTL = 86400  # 24 hours in seconds


class RateLimiter:
    """Simple rate limiter for web requests."""
    
    def __init__(self, delay: float = REQUEST_DELAY):
        self.delay = delay
        self.last_request_time = 0.0
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait before allowing next request."""
        async with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.delay:
                await asyncio.sleep(self.delay - time_since_last)
            self.last_request_time = time.time()


# Global rate limiter
_rate_limiter = RateLimiter()


def get_cache_key(url: str) -> str:
    """Generate cache key for URL."""
    return hashlib.md5(url.encode()).hexdigest()


def get_cache_file(cache_key: str) -> Path:
    """Get cache file path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{cache_key}.json"


def load_from_cache(url: str) -> Optional[dict]:
    """Load cached result if available and not expired."""
    try:
        cache_key = get_cache_key(url)
        cache_file = get_cache_file(cache_key)
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
        
        # Check if cache is expired
        cached_time = cached_data.get('cached_at', 0)
        if time.time() - cached_time > CACHE_TTL:
            logger.info(f"Cache expired for {url}")
            cache_file.unlink()
            return None
        
        logger.info(f"Using cached result for {url}")
        return cached_data.get('data')
    
    except Exception as e:
        logger.warning(f"Failed to load from cache: {e}")
        return None


def save_to_cache(url: str, data: dict):
    """Save result to cache."""
    try:
        cache_key = get_cache_key(url)
        cache_file = get_cache_file(cache_key)
        
        cache_data = {
            'cached_at': time.time(),
            'url': url,
            'data': data
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cached result for {url}")
    
    except Exception as e:
        logger.warning(f"Failed to save to cache: {e}")


async def _fetch_with_httpx(url: str, timeout: int) -> Optional[str]:
    """Try fetching with httpx. Returns HTML or None on failure."""
    await _rate_limiter.acquire()
    
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=BROWSER_HEADERS)
                
                if response.status_code == 403:
                    logger.info(f"httpx got 403 for {url}, will try Playwright")
                    return None
                    
                if response.status_code == 429:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    logger.warning(f"Rate limited for {url}, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response.text
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout for {url} (attempt {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            logger.info(f"httpx failed for {url} (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    
    logger.error(f"All httpx attempts failed for {url}")
    return None


def _fetch_with_playwright(url: str, timeout: int) -> Optional[str]:
    """Fallback: fetch with Playwright (headless) for bot-protected sites."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not installed, cannot use browser fallback")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,  # Changed to headless for production
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox"
                ],
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
            
            # Navigate with error handling
            try:
                page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            except Exception as e:
                logger.warning(f"Playwright navigation failed for {url}: {e}")
                browser.close()
                return None
            
            # Wait for content to load
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()

            # Check for access denied
            if "Access Denied" in html and len(html) < 1000:
                logger.warning(f"Playwright also got Access Denied for {url}")
                return None
            
            return html
            
    except Exception as e:
        logger.error(f"Playwright failed for {url}: {e}")
        return None


async def crawl_url(url: str, use_cache: bool = True) -> dict:
    """Crawl a single URL and extract text content with improved stability.

    Args:
        url: URL to crawl
        use_cache: Whether to use cached results
        
    Returns:
        dict with keys: url, title, text, links, error (if any)
    """
    # Check cache first
    if use_cache:
        cached_result = load_from_cache(url)
        if cached_result:
            return cached_result
    
    timeout = config.crawler.timeout_seconds
    
    # Try httpx first (fast)
    html = await _fetch_with_httpx(url, timeout)
    
    # Fallback to Playwright for protected sites
    if html is None:
        logger.info(f"Trying Playwright fallback for {url}")
        html = await asyncio.to_thread(_fetch_with_playwright, url, timeout)

    if html is None:
        result = {
            "url": url,
            "title": "",
            "text": "",
            "links": [],
            "error": "Website konnte nicht gecrawlt werden (möglicherweise blockiert oder offline)"
        }
        return result
    
    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    text = soup.get_text(separator="\n", strip=True)
    
    # Clean up text
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    
    # Truncate very long pages
    if len(text) > 15000:
        text = text[:15000] + "\n...[Text gekürzt]"

    # Extract internal links
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base, href)
        if full_url.startswith(base) and full_url not in links:
            links.append(full_url)

    result = {
        "url": url,
        "title": title,
        "text": text,
        "links": links[:20],  # Limit links
        "cached": False
    }
    
    # Cache successful results
    if not result.get("error"):
        save_to_cache(url, result)
    
    return result


async def crawl_website(base_url: str, progress_callback=None) -> list[dict]:
    """Crawl a website starting from the base URL, prioritizing important pages.

    Args:
        base_url: Base URL of the website
        progress_callback: Optional callback function(current, total, message)
        
    Returns:
        list of page dicts
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
    errors = []

    for i, url in enumerate(urls_to_crawl):
        if len(crawled) >= max_pages:
            break
        if url in seen:
            continue
        seen.add(url)

        # Report progress
        if progress_callback:
            progress_callback(i + 1, min(len(urls_to_crawl), max_pages), f"Crawling: {url}")

        try:
            result = await crawl_url(url)
            
            if result.get("error"):
                errors.append(result)
                logger.warning(f"Failed to crawl {url}: {result['error']}")
            elif result.get("text"):
                crawled.append(result)
                logger.info(f"Successfully crawled {url} ({len(result['text'])} chars)")
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            errors.append({
                "url": url,
                "error": str(e)
            })

    logger.info(f"Crawling complete: {len(crawled)} pages successfully, {len(errors)} errors")
    
    if errors and progress_callback:
        progress_callback(len(crawled), len(crawled) + len(errors), 
                         f"Complete with {len(errors)} errors")

    return crawled
