"""Outreach agent node - generates personalized contact requests."""

import json

from langchain_core.messages import AIMessage, SystemMessage
from sqlalchemy import select

from app.agents.state import AgentState
from app.db.engine import async_session
from app.db.models import UserProfile, Template
from app.services.llm import get_agent_llm

OUTREACH_PROMPT = """Du bist ein Experte fuer personalisierte Geschaeftskommunikation. Erstelle eine {format_type} basierend auf:

**Firmenprofil (Empfaenger):**
{company_profile}

**Nutzerprofil (Absender):**
{user_profile}

{template_section}

Erstelle eine professionelle, persoenliche {format_type} die:
- Auf die spezifischen Beduerfnisse und Leistungen der Firma eingeht
- Die passenden Angebote des Nutzers hervorhebt
- Einen konkreten Mehrwert kommuniziert
- Einen klaren Call-to-Action hat
- In einem freundlichen, professionellen Ton geschrieben ist

Zeige die fertige {format_type} und frage ob der Nutzer Aenderungen wuenscht oder sie als Vorlage speichern moechte.
Antworte auf Deutsch."""


async def outreach_node(state: AgentState) -> dict:
    """Generate personalized outreach content."""
    company_profile = state.get("company_profile")
    messages = state["messages"]

    if not company_profile:
        return {
            "messages": [AIMessage(content="Ich brauche zuerst ein Firmenprofil. Bitte waehle eine Firma aus und lass mich einen Steckbrief erstellen.")],
        }

    # Determine format type from user message
    last_msg = messages[-1]
    user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    user_text_lower = user_text.lower()

    if "landing" in user_text_lower or "seite" in user_text_lower:
        format_type = "Landing Page"
    elif "telefon" in user_text_lower or "anruf" in user_text_lower or "script" in user_text_lower:
        format_type = "Telefonskript"
    else:
        format_type = "E-Mail"

    # Load user profile
    user_profile_text = "Nicht verfuegbar"
    async with async_session() as db:
        result = await db.execute(select(UserProfile).limit(1))
        user_profile = result.scalar_one_or_none()
        if user_profile and user_profile.company_name:
            offerings = json.loads(user_profile.offerings_json) if user_profile.offerings_json else []
            strengths = json.loads(user_profile.strengths_json) if user_profile.strengths_json else []
            user_profile_text = f"""Firmenname: {user_profile.company_name}
Angebote: {', '.join(offerings)}
Staerken: {', '.join(strengths)}"""

    # Check for matching template
    template_section = ""
    async with async_session() as db:
        category = {"E-Mail": "email", "Landing Page": "landing_page", "Telefonskript": "phone_script"}.get(format_type, "email")
        result = await db.execute(
            select(Template).where(Template.category == category).limit(1)
        )
        template = result.scalar_one_or_none()
        if template:
            template_section = f"\n**Vorlage als Orientierung:**\n{template.content}\n"

    # Format company profile
    cp = company_profile
    company_text = f"""Firmenname: {cp.get('name', '')}
Leistungen: {', '.join(cp.get('services', []))}
Beschreibung: {cp.get('description', '')}
Team: {', '.join(cp.get('team', []))}
USP: {cp.get('usp', '')}"""

    llm = get_agent_llm()
    response = await llm.ainvoke([
        SystemMessage(content=OUTREACH_PROMPT.format(
            format_type=format_type,
            company_profile=company_text,
            user_profile=user_profile_text,
            template_section=template_section,
        )),
        *messages,
    ])

    return {
        "messages": [response],
        "generated_content": response.content if hasattr(response, "content") else str(response),
        "current_phase": "done",
    }
