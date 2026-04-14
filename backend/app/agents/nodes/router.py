"""Intent classification router node."""

import logging

from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.services.llm import get_router_llm

logger = logging.getLogger(__name__)

VALID_INTENTS = {"search", "crawl_url", "matching", "outreach", "user_profile", "template", "knowledge", "general_chat"}


class IntentClassification(BaseModel):
    """Classified intent from user message."""
    intent: str = Field(
        description="The classified intent. One of: search, crawl_url, matching, outreach, user_profile, template, knowledge, general_chat"
    )
    reasoning: str = Field(description="Brief reasoning for the classification")


ROUTER_SYSTEM_PROMPT = """Du bist ein Intent-Klassifikator fuer ein Werbesystem. Analysiere die letzte Nachricht des Nutzers und klassifiziere den Intent.

Moegliche Intents:
- search: Nutzer will nach Firmen/Kunden suchen (z.B. "Zahnarzt in Luebeck", "suche Restaurants")
- crawl_url: Nutzer gibt eine URL an die gecrawlt werden soll (z.B. "schau dir www.example.de an")
- matching: Nutzer will wissen was er einer Firma anbieten kann, Matching zwischen eigenem Profil und Firmenprofil
- outreach: Nutzer will eine Kontaktanfrage erstellen (Email, Landing Page, Telefonskript)
- user_profile: Nutzer spricht ueber sein eigenes Unternehmen/Profil/Angebote (z.B. "ich biete Webdesign an", "wir sind ein FabLab")
- template: Nutzer will Vorlagen verwalten (erstellen, bearbeiten, auflisten)
- knowledge: Nutzer will Wissen speichern oder abrufen (z.B. "merke dir...")
- general_chat: Allgemeine Frage oder Konversation die in keine andere Kategorie passt

Klassifiziere basierend auf der letzten Nachricht im Kontext der Konversation."""


async def router_node(state: AgentState) -> dict:
    """Classify the user's intent using structured output."""
    llm = get_router_llm()

    try:
        structured_llm = llm.with_structured_output(IntentClassification)
        result = await structured_llm.ainvoke([
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            *state["messages"][-3:],
        ])
        intent = result.intent.strip().lower()
        if intent not in VALID_INTENTS:
            logger.warning(f"Router returned invalid intent: {intent}")
            intent = "general_chat"
        logger.info(f"Router classified: {intent} ({result.reasoning})")
        return {"intent": intent}
    except Exception as e:
        logger.warning(f"Router failed: {e}")
        return {"intent": "general_chat"}
