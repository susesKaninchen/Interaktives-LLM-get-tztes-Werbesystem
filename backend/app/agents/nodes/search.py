"""Search agent node - searches for businesses and presents results."""

import logging

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.agents.tools.web_search import search_web
from app.services.llm import get_agent_llm

logger = logging.getLogger(__name__)

SEARCH_PRESENT_PROMPT = """Du bist ein Assistent der Suchergebnisse praesentiert. Hier sind die Ergebnisse einer Websuche:

{results}

Praesentiere die Ergebnisse als nummerierte Liste mit Titel, URL und kurzer Beschreibung.
Frage den Nutzer, welche Firma er naeher untersuchen moechte, oder ob er eine neue Suche starten will.
Sei freundlich und hilfsbereit. Antworte auf Deutsch."""


class SearchQuery(BaseModel):
    query: str = Field(description="The search query to use for DuckDuckGo")


async def search_node(state: AgentState) -> dict:
    """Search for businesses based on user input."""
    llm = get_agent_llm()
    messages = state["messages"]

    # Extract search query from user message
    try:
        structured_llm = llm.with_structured_output(SearchQuery)
        result = await structured_llm.ainvoke([
            SystemMessage(content="Extrahiere eine Suchanfrage aus der Nachricht. Beispiel: 'Zahnarzt in Luebeck' -> query='Zahnarzt Luebeck'"),
            messages[-1],
        ])
        query = result.query
    except Exception as e:
        logger.warning(f"Query extraction failed: {e}")
        last_msg = messages[-1]
        query = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    logger.info(f"Searching for: {query}")

    # Perform web search
    results = await search_web(query)

    if not results:
        return {
            "messages": [AIMessage(content="Leider konnte ich keine Ergebnisse finden. Versuche es mit anderen Suchbegriffen.")],
            "search_results": [],
        }

    # Format results for presentation
    results_text = "\n".join(
        f"{i+1}. **{r['title']}**\n   URL: {r['url']}\n   {r['description']}"
        for i, r in enumerate(results)
    )

    # Generate presentation with LLM
    response = await llm.ainvoke([
        SystemMessage(content=SEARCH_PRESENT_PROMPT.format(results=results_text)),
        *messages,
    ])

    return {
        "messages": [response],
        "search_results": results,
        "current_phase": "select",
    }
