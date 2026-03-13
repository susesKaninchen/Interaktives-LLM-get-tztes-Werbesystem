"""Template manager agent node - manages outreach templates."""

import json

from langchain_core.messages import AIMessage, SystemMessage
from sqlalchemy import select

from app.agents.state import AgentState
from app.db.engine import async_session
from app.db.models import Template
from app.services.llm import get_agent_llm

LIST_TEMPLATES_PROMPT = """Hier sind die verfuegbaren Vorlagen:

{templates}

Praesentiere die Vorlagen uebersichtlich. Frage den Nutzer ob er eine Vorlage bearbeiten, loeschen oder eine neue erstellen moechte.
Antworte auf Deutsch."""


async def template_mgr_node(state: AgentState) -> dict:
    """Manage templates - list, create, update."""
    messages = state["messages"]
    last_msg = messages[-1]
    user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # Check if user wants to save current generated content as template
    generated = state.get("generated_content", "")
    if generated and ("vorlage" in user_text.lower() or "speicher" in user_text.lower()):
        # Determine category
        if "landing" in user_text.lower():
            category = "landing_page"
        elif "telefon" in user_text.lower():
            category = "phone_script"
        else:
            category = "email"

        async with async_session() as db:
            template = Template(
                name=f"Vorlage {category}",
                category=category,
                content=generated,
            )
            db.add(template)
            await db.commit()

        return {
            "messages": [AIMessage(content=f"Die Vorlage wurde als '{category}' gespeichert! Du kannst sie in zukuenftigen Kontaktanfragen verwenden.")],
        }

    # List existing templates
    async with async_session() as db:
        result = await db.execute(select(Template).order_by(Template.created_at.desc()))
        templates = result.scalars().all()

    if not templates:
        return {
            "messages": [AIMessage(content="Es gibt noch keine Vorlagen. Erstelle zuerst eine Kontaktanfrage und speichere sie als Vorlage.")],
        }

    templates_text = "\n\n".join(
        f"**{t.name}** (Kategorie: {t.category})\n{t.content[:200]}..."
        for t in templates
    )

    llm = get_agent_llm()
    response = await llm.ainvoke([
        SystemMessage(content=LIST_TEMPLATES_PROMPT.format(templates=templates_text)),
        *messages,
    ])

    return {"messages": [response]}
