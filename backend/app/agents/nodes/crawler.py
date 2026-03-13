"""Crawler agent node - crawls websites and extracts information."""

import json
import re

from langchain_core.messages import AIMessage, SystemMessage

from app.agents.state import AgentState
from app.agents.tools.web_crawler import crawl_website
from app.services.llm import get_agent_llm

CRAWL_SUMMARY_PROMPT = """Du hast die Website einer Firma gecrawlt. Hier sind die extrahierten Inhalte:

{content}

Erstelle eine uebersichtliche Zusammenfassung mit:
- Firmenname
- Was die Firma macht / Leistungen
- Standort / Adresse (wenn vorhanden)
- Team / Ansprechpartner (wenn vorhanden)
- Besonderheiten / USP

Frage den Nutzer dann, ob er einen detaillierten Steckbrief erstellen lassen moechte oder ob er weitere Infos braucht.
Antworte auf Deutsch."""


def extract_url_from_message(text: str) -> str | None:
    """Extract a URL from a message text."""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None


def extract_url_from_selection(text: str, search_results: list[dict]) -> str | None:
    """Try to match user selection to a search result."""
    text_lower = text.lower().strip()

    # Check for number selection ("nimm den 3.", "Nummer 2", etc.)
    num_match = re.search(r'(\d+)', text)
    if num_match:
        idx = int(num_match.group(1)) - 1
        if 0 <= idx < len(search_results):
            return search_results[idx].get("url")

    # Check for name match
    for result in search_results:
        title = result.get("title", "").lower()
        if title and any(word in text_lower for word in title.split() if len(word) > 3):
            return result.get("url")

    return None


async def crawler_node(state: AgentState) -> dict:
    """Crawl a website and summarize the content."""
    messages = state["messages"]
    search_results = state.get("search_results", [])
    last_msg = messages[-1]
    user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # Try to get URL from message directly, or from selection
    url = extract_url_from_message(user_text)
    if not url:
        url = extract_url_from_selection(user_text, search_results)

    if not url:
        return {
            "messages": [AIMessage(
                content="Ich konnte keine URL erkennen. Bitte gib die URL der Website an, die ich crawlen soll, oder waehle eine Firma aus der Liste."
            )],
        }

    # Crawl the website
    pages = await crawl_website(url)

    if not pages:
        return {
            "messages": [AIMessage(
                content=f"Leider konnte ich die Website {url} nicht erreichen. Pruefe bitte die URL und versuche es erneut."
            )],
        }

    # Combine page contents
    combined_content = "\n\n---\n\n".join(
        f"Seite: {p['title']} ({p['url']})\n{p['text'][:3000]}"
        for p in pages
    )

    # Summarize with LLM
    llm = get_agent_llm()
    response = await llm.ainvoke([
        SystemMessage(content=CRAWL_SUMMARY_PROMPT.format(content=combined_content[:8000])),
        *messages,
    ])

    # Store selected company info
    selected_company = {
        "url": url,
        "pages": pages,
        "title": pages[0].get("title", "") if pages else "",
    }

    return {
        "messages": [response],
        "selected_company": selected_company,
        "current_phase": "profile",
    }
