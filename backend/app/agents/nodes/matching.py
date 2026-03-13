"""Matching agent node - compares company profile with user profile."""

import json

from langchain_core.messages import AIMessage, SystemMessage
from sqlalchemy import select

from app.agents.state import AgentState
from app.db.engine import async_session
from app.db.models import UserProfile
from app.services.llm import get_agent_llm

MATCHING_PROMPT = """Du bist ein Matching-Experte. Vergleiche das Firmenprofil eines potenziellen Kunden mit dem Profil des Nutzers und finde passende Angebote.

**Firmenprofil (potenzieller Kunde):**
{company_profile}

**Nutzerprofil (eigenes Unternehmen):**
{user_profile}

Erstelle eine Analyse:
1. Welche Angebote des Nutzers passen zu den Beduerfnissen der Firma?
2. Welche konkreten Vorteile kann der Nutzer dieser Firma bieten?
3. Welcher Ansprechpartner waere am besten geeignet?
4. Empfohlene Ansprache-Strategie

Frage am Ende ob der Nutzer eine Kontaktanfrage erstellen moechte.
Antworte auf Deutsch."""


async def matching_node(state: AgentState) -> dict:
    """Match company profile with user profile and suggest opportunities."""
    company_profile = state.get("company_profile")

    if not company_profile:
        return {
            "messages": [AIMessage(
                content="Ich habe noch kein Firmenprofil. Bitte waehle zuerst eine Firma aus und lass mich einen Steckbrief erstellen."
            )],
        }

    # Load user profile
    user_profile_text = "Noch kein Profil vorhanden. Bitte erzaehle mir zuerst ueber dein Unternehmen."
    async with async_session() as db:
        result = await db.execute(select(UserProfile).limit(1))
        user_profile = result.scalar_one_or_none()

        if user_profile and user_profile.company_name:
            offerings = json.loads(user_profile.offerings_json) if user_profile.offerings_json else []
            targets = json.loads(user_profile.target_markets_json) if user_profile.target_markets_json else []
            strengths = json.loads(user_profile.strengths_json) if user_profile.strengths_json else []

            user_profile_text = f"""Firmenname: {user_profile.company_name}
Angebote: {', '.join(offerings) if offerings else 'Nicht angegeben'}
Zielmaerkte: {', '.join(targets) if targets else 'Nicht angegeben'}
Staerken: {', '.join(strengths) if strengths else 'Nicht angegeben'}"""
        else:
            return {
                "messages": [AIMessage(
                    content="Ich brauche zuerst Informationen ueber dein eigenes Unternehmen, um ein gutes Matching zu machen. Erzaehl mir von deiner Firma: Was bietest du an? Wer ist deine Zielgruppe?"
                )],
            }

    # Format company profile
    cp = company_profile
    company_text = f"""Firmenname: {cp.get('name', '')}
Website: {cp.get('website', '')}
Leistungen: {', '.join(cp.get('services', [])) if cp.get('services') else 'Nicht bekannt'}
Beschreibung: {cp.get('description', '')}
USP: {cp.get('usp', '')}
Team: {', '.join(cp.get('team', [])) if cp.get('team') else 'Nicht bekannt'}"""

    llm = get_agent_llm()
    response = await llm.ainvoke([
        SystemMessage(content=MATCHING_PROMPT.format(
            company_profile=company_text,
            user_profile=user_profile_text,
        )),
        *state["messages"],
    ])

    return {
        "messages": [response],
        "current_phase": "contact",
    }
