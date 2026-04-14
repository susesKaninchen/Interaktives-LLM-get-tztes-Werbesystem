"""Knowledge agent node - manages cross-conversation insights."""

import json
import logging

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.agents.state import AgentState
from app.db.engine import async_session
from app.db.models import KnowledgeEntry
from app.db.vector_store import get_knowledge_collection
from app.services.llm import get_agent_llm

logger = logging.getLogger(__name__)


async def get_relevant_knowledge(query: str, n_results: int = 5) -> list[str]:
    """Retrieve relevant knowledge entries for a query."""
    collection = get_knowledge_collection()
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        if results and results.get("documents"):
            return results["documents"][0]
    except Exception:
        pass
    return []


async def get_all_knowledge() -> list[dict]:
    """Get all knowledge entries."""
    async with async_session() as db:
        result = await db.execute(select(KnowledgeEntry).order_by(KnowledgeEntry.created_at.desc()))
        return [
            {
                "id": e.id,
                "content": e.content,
                "tags": json.loads(e.tags_json) if e.tags_json else [],
            }
            for e in result.scalars().all()
        ]


class Insight(BaseModel):
    content: str = Field(description="The knowledge/insight to save as a clear sentence")
    tags: list[str] = Field(default_factory=list, description="2-4 relevant tags")


KNOWLEDGE_PROMPT = """Du verwaltest die Wissensbasis des Nutzers. Hier sind die aktuellen Eintraege:

{entries}

Der Nutzer moechte Wissen verwalten. Praesentiere die Eintraege und frage ob er neue Erkenntnisse hinzufuegen, bestehende loeschen oder nach bestimmtem Wissen suchen moechte.
Antworte auf Deutsch."""


async def knowledge_node(state: AgentState) -> dict:
    """Manage knowledge base entries."""
    messages = state["messages"]
    last_msg = messages[-1]
    user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # Check if user wants to save something
    if any(word in user_text.lower() for word in ["speicher", "merk", "merke", "notier"]):
        llm = get_agent_llm()
        try:
            structured_llm = llm.with_structured_output(Insight)
            insight = await structured_llm.ainvoke([
                SystemMessage(content="Extrahiere die Erkenntnis/das Wissen das der Nutzer speichern moechte. Formuliere es klar und praegnant."),
                *messages[-3:],
            ])

            async with async_session() as db:
                entry = KnowledgeEntry(
                    content=insight.content,
                    tags_json=json.dumps(insight.tags, ensure_ascii=False),
                    source_conversation_id=state.get("conversation_id"),
                )
                db.add(entry)
                await db.commit()

                # Store in ChromaDB
                collection = get_knowledge_collection()
                collection.upsert(
                    ids=[f"knowledge_{entry.id}"],
                    documents=[insight.content],
                    metadatas=[{"tags": ",".join(insight.tags)}],
                )

            return {
                "messages": [AIMessage(content=f"Erkenntnis gespeichert: \"{insight.content}\"\nTags: {', '.join(insight.tags) if insight.tags else 'keine'}")],
            }
        except Exception as e:
            logger.error(f"Knowledge save failed: {e}")
            return {
                "messages": [AIMessage(content="Ich konnte die Erkenntnis nicht verarbeiten. Bitte formuliere sie nochmal.")],
            }

    # Show existing knowledge
    entries = await get_all_knowledge()
    if not entries:
        return {
            "messages": [AIMessage(content="Die Wissensbasis ist noch leer. Sage mir etwas, das ich mir merken soll!")],
        }

    entries_text = "\n".join(
        f"- {e['content']} (Tags: {', '.join(e['tags'])})" for e in entries
    )

    llm = get_agent_llm()
    response = await llm.ainvoke([
        SystemMessage(content=KNOWLEDGE_PROMPT.format(entries=entries_text)),
        *messages[-3:],
    ])

    return {"messages": [response]}
