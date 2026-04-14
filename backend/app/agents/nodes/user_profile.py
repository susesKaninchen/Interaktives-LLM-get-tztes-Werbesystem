"""User profile agent node - manages the user's own business profile."""

import json
import logging

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.db.engine import async_session
from app.db.models import UserProfile
from app.services.llm import get_agent_llm

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """Analysiere die Nachrichten des Nutzers und extrahiere Informationen ueber sein Unternehmen/Profil.
Aktualisiere die bestehenden Informationen mit neuen Details.

Bestehendes Profil:
{existing}

Extrahiere alle relevanten Business-Informationen."""


class UserProfileData(BaseModel):
    company_name: str = Field(default="", description="Firmenname des Nutzers")
    offerings: list[str] = Field(default_factory=list, description="Angebote/Dienstleistungen")
    target_markets: list[str] = Field(default_factory=list, description="Zielmaerkte/Branchen")
    strengths: list[str] = Field(default_factory=list, description="Staerken/USPs")


PRESENT_PROMPT = """Hier ist das aktualisierte Profil des Nutzers:

{profile}

Fasse das Profil zusammen und frage ob es korrekt ist oder ob der Nutzer etwas aendern moechte.
Erklaere wie dieses Profil beim Matching mit potenziellen Kunden helfen wird.
Antworte auf Deutsch."""


async def user_profile_node(state: AgentState) -> dict:
    """Extract and update the user's business profile."""
    llm = get_agent_llm()

    # Load existing profile
    existing_text = "Noch kein Profil vorhanden."
    async with async_session() as db:
        from sqlalchemy import select
        result = await db.execute(select(UserProfile).limit(1))
        existing = result.scalar_one_or_none()
        if existing:
            offerings = json.loads(existing.offerings_json) if existing.offerings_json else []
            targets = json.loads(existing.target_markets_json) if existing.target_markets_json else []
            strengths = json.loads(existing.strengths_json) if existing.strengths_json else []
            existing_text = f"""Firmenname: {existing.company_name or ''}
Angebote: {', '.join(offerings)}
Zielmaerkte: {', '.join(targets)}
Staerken: {', '.join(strengths)}"""

    # Extract profile data
    try:
        structured_llm = llm.with_structured_output(UserProfileData)
        profile_data = await structured_llm.ainvoke([
            SystemMessage(content=EXTRACT_PROMPT.format(existing=existing_text)),
            *state["messages"][-5:],
        ])
    except Exception as e:
        logger.error(f"Profile extraction failed: {e}")
        return {
            "messages": [AIMessage(content="Ich konnte die Informationen nicht richtig verarbeiten. Kannst du mir mehr ueber dein Unternehmen erzaehlen?")],
        }

    # Save to database
    async with async_session() as db:
        from sqlalchemy import select
        result = await db.execute(select(UserProfile).limit(1))
        profile = result.scalar_one_or_none()

        if profile is None:
            profile = UserProfile()
            db.add(profile)

        if profile_data.company_name:
            profile.company_name = profile_data.company_name
        if profile_data.offerings:
            profile.offerings_json = json.dumps(profile_data.offerings, ensure_ascii=False)
        if profile_data.target_markets:
            profile.target_markets_json = json.dumps(profile_data.target_markets, ensure_ascii=False)
        if profile_data.strengths:
            profile.strengths_json = json.dumps(profile_data.strengths, ensure_ascii=False)

        # Store raw text of last user message as notes
        last_msg = state["messages"][-1]
        raw = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        existing_notes = profile.raw_notes or ""
        profile.raw_notes = f"{existing_notes}\n{raw}".strip()

        await db.commit()

    # Present updated profile
    profile_text = f"""**{profile_data.company_name}**
Angebote: {', '.join(profile_data.offerings) if profile_data.offerings else 'Noch nicht angegeben'}
Zielmaerkte: {', '.join(profile_data.target_markets) if profile_data.target_markets else 'Noch nicht angegeben'}
Staerken: {', '.join(profile_data.strengths) if profile_data.strengths else 'Noch nicht angegeben'}"""

    response = await llm.ainvoke([
        SystemMessage(content=PRESENT_PROMPT.format(profile=profile_text)),
        *state["messages"][-3:],
    ])

    return {
        "messages": [response],
        "user_profile": profile_data.model_dump(),
    }
