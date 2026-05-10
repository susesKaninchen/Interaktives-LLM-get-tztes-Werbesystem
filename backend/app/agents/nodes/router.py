"""Intent classification router node with improved context handling."""

import logging
from typing import Optional

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
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")


ROUTER_SYSTEM_PROMPT = """Du bist ein Intent-Klassifikator fuer ein Werbesystem. Analysiere die letzten Nachrichten des Nutzers und klassifiziere den Intent.

Moegliche Intents:
- search: Nutzer will nach Firmen/Kunden suchen (z.B. "Zahnarzt in Luebeck", "suche Restaurants", "finde Softwarefirmen")
- crawl_url: Nutzer gibt eine URL an die gecrawlt werden soll (z.B. "schau dir www.example.de an", "analysiere diese Webseite")
- matching: Nutzer will wissen was er einer Firma anbieten kann, Matching zwischen eigenem Profil und Firmenprofil
- outreach: Nutzer will eine Kontaktanfrage erstellen (Email, Landing Page, Telefonskript)
- user_profile: Nutzer spricht ueber sein eigenes Unternehmen/Profil/Angebote (z.B. "ich biete Webdesign an", "wir sind ein FabLab")
- template: Nutzer will Vorlagen verwalten (erstellen, bearbeiten, auflisten)
- knowledge: Nutzer will Wissen speichern oder abrufen (z.B. "merke dir...", "was hast du gespeichert")
- general_chat: Allgemeine Frage oder Konversation die in keine andere Kategorie passt

Kontext-Berücksichtigung:
- Berücksichtige die aktuelle Phase der Konversation
- Schau auf vorhandene Firmen- und Benutzerdaten
- Sei konsistent mit vorherigen Klassifizierungen
- Bei unsicheren Fällen wähle "general_chat"

Klassifiziere basierend auf den letzten Nachrichten im Kontext der Konversation."""


async def router_node(state: AgentState) -> dict:
    """Classify the user's intent using structured output with enhanced context."""
    llm = get_router_llm()
    
    # Determine context window based on conversation length
    messages = state["messages"]
    context_size = min(len(messages), 10)  # Increased from 3 to 10 for better context
    
    # Build context description for the LLM
    context_description = f"""
Aktuelle Phase: {state.get('current_phase', 'search')}
Vorhandene Suchergebnisse: {'Ja' if state.get('search_results') else 'Nein'}
Ausgewählte Firma: {'Ja' if state.get('selected_company') else 'Nein'}
Firmenprofil: {'Ja' if state.get('company_profile') else 'Nein'}
Benutzerprofil: {'Ja' if state.get('user_profile') else 'Nein'}
Matching-Ergebnisse: {'Ja' if state.get('matching_results') else 'Nein'}
"""
    
    try:
        structured_llm = llm.with_structured_output(IntentClassification, include_raw=False)
        enhanced_system_prompt = ROUTER_SYSTEM_PROMPT + "\n\n" + context_description
        
        result = await structured_llm.ainvoke([
            SystemMessage(content=enhanced_system_prompt),
            *messages[-context_size:],  # Use more context for better classification
        ])
        
        intent = result.intent.strip().lower()
        
        # Validate intent
        if intent not in VALID_INTENTS:
            logger.warning(f"Router returned invalid intent: {intent}, defaulting to general_chat")
            intent = "general_chat"
        
        # Check confidence level
        if result.confidence < 0.5:
            logger.warning(f"Low confidence classification: {intent} (confidence: {result.confidence})")
            # Could implement fallback logic here
        
        logger.info(f"Router classified: {intent} (confidence: {result.confidence}, reasoning: {result.reasoning})")
        return {"intent": intent}
        
    except Exception as e:
        logger.error(f"Router failed: {e}", exc_info=True)
        
        # Enhanced fallback: try simple keyword matching
        fallback_intent = _fallback_intent_classification(messages)
        if fallback_intent:
            logger.info(f"Using fallback intent: {fallback_intent}")
            return {"intent": fallback_intent}
        
        return {"intent": "general_chat"}


def _fallback_intent_classification(messages) -> Optional[str]:
    """Simple keyword-based fallback classification."""
    if not messages:
        return None
    
    last_message = messages[-1]
    content = last_message.content.lower() if hasattr(last_message, "content") else str(last_message).lower()
    
    # Simple keyword matching
    keywords = {
        "search": ["suche", "finde", "such nach", "lokale", "in der nähe", "unternehmen", "firma"],
        "crawl_url": ["www.", "http", "website", "webseite", "schau dir an", "analysiere", "crawle"],
        "matching": ["matching", "passende", "angebot", "was kann ich", "wie passt", "vergleiche"],
        "outreach": ["email", "kontakt", "anschreiben", "nachricht", "telefon", "ansprechen"],
        "user_profile": ["ich biete", "wir sind", "mein unternehmen", "unsere leistungen", "profil"],
        "template": ["vorlage", "template", "erstellen", "bearbeiten", "verwalten"],
        "knowledge": ["merke dir", "speichern", "was weißt du", "gespeichert", "wissen"]
    }
    
    for intent, words in keywords.items():
        if any(word in content for word in words):
            return intent
    
    return None
