"""DuckDuckGo web search tool."""

import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


async def search_web(query: str, max_results: int = 10) -> list[dict]:
    """Search the web using DuckDuckGo and return results.

    Returns list of dicts with keys: title, url, description.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", r.get("link", "")),
                "description": r.get("body", r.get("snippet", "")),
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []
