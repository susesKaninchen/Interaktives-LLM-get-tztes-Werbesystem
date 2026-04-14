"""Profile builder agent node - creates structured company profiles."""

import json
import logging

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.db.engine import async_session
from app.db.models import CompanyProfile
from app.db.vector_store import store_website_content
from app.services.llm import get_agent_llm

logger = logging.getLogger(__name__)

PROFILE_EXTRACT_PROMPT = """Analysiere die folgenden Website-Inhalte und extrahiere ein strukturiertes Firmenprofil.

Website-Inhalte:
{content}

Extrahiere so viele Informationen wie moeglich. Wenn eine Information nicht verfuegbar ist, lasse das Feld leer."""


class CompanyProfileData(BaseModel):
    name: str = Field(default="", description="Firmenname")
    website: str = Field(default="", description="Website URL")
    address: str = Field(default="", description="Adresse")
    phone: str = Field(default="", description="Telefonnummer")
    email: str = Field(default="", description="E-Mail")
    services: list[str] = Field(default_factory=list, description="Leistungen/Services")
    team: list[str] = Field(default_factory=list, description="Teammitglieder/Ansprechpartner")
    description: str = Field(default="", description="Kurze Beschreibung der Firma")
    usp: str = Field(default="", description="Alleinstellungsmerkmal / USP")


PROFILE_PRESENT_PROMPT = """Hier ist das Firmenprofil das ich erstellt habe:

{profile}

Praesentiere dieses Profil uebersichtlich als Steckbrief mit Markdown-Formatierung.
Frage den Nutzer, ob das Profil passt oder ob er Aenderungen/mehr Details moechte.
Schlage vor, als naechstes ein Matching mit den eigenen Angeboten zu machen.
Antworte auf Deutsch."""


async def profile_builder_node(state: AgentState) -> dict:
    """Build a structured company profile from crawled content."""
    conversation_id = state["conversation_id"]
    selected_company = state.get("selected_company")

    if not selected_company or not selected_company.get("pages"):
        return {
            "messages": [AIMessage(content="Ich habe noch keine Firma gecrawlt. Bitte waehle zuerst eine Firma aus oder gib eine URL an.")],
        }

    pages = selected_company["pages"]

    # Store in ChromaDB for future queries
    store_website_content(conversation_id, pages)

    # Combine content for profile extraction
    combined = "\n\n---\n\n".join(
        f"Seite: {p.get('title', '')} ({p.get('url', '')})\n{p.get('text', '')[:3000]}"
        for p in pages
    )

    llm = get_agent_llm()

    # Extract structured profile
    try:
        structured_llm = llm.with_structured_output(CompanyProfileData)
        profile_data = await structured_llm.ainvoke([
            SystemMessage(content=PROFILE_EXTRACT_PROMPT.format(content=combined[:8000])),
        ])
    except Exception as e:
        logger.error(f"Profile extraction failed: {e}")
        profile_data = CompanyProfileData(
            name=selected_company.get("title", ""),
            website=selected_company.get("url", ""),
        )

    # Ensure website is set
    if not profile_data.website:
        profile_data.website = selected_company.get("url", "")

    # Save to database
    async with async_session() as db:
        profile = CompanyProfile(
            conversation_id=conversation_id,
            name=profile_data.name,
            website=profile_data.website,
            address=profile_data.address,
            phone=profile_data.phone,
            email=profile_data.email,
            services_json=json.dumps(profile_data.services, ensure_ascii=False),
            team_json=json.dumps(profile_data.team, ensure_ascii=False),
            description=profile_data.description,
            usp=profile_data.usp,
            raw_content=combined[:10000],
        )
        db.add(profile)
        await db.commit()

    # Format for presentation
    profile_text = f"""**{profile_data.name}**
Website: {profile_data.website}
Adresse: {profile_data.address or 'Nicht verfuegbar'}
Telefon: {profile_data.phone or 'Nicht verfuegbar'}
E-Mail: {profile_data.email or 'Nicht verfuegbar'}

**Leistungen:** {', '.join(profile_data.services) if profile_data.services else 'Nicht verfuegbar'}
**Team:** {', '.join(profile_data.team) if profile_data.team else 'Nicht verfuegbar'}
**Beschreibung:** {profile_data.description or 'Nicht verfuegbar'}
**USP:** {profile_data.usp or 'Nicht verfuegbar'}"""

    response = await llm.ainvoke([
        SystemMessage(content=PROFILE_PRESENT_PROMPT.format(profile=profile_text)),
        *state["messages"],
    ])

    return {
        "messages": [response],
        "company_profile": profile_data.model_dump(),
        "current_phase": "matching",
    }
