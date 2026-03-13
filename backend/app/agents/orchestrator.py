"""LangGraph orchestrator - main agent graph."""

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.agents.state import AgentState
from app.agents.nodes.router import router_node
from app.agents.nodes.search import search_node
from app.agents.nodes.crawler import crawler_node
from app.services.llm import get_agent_llm

SYSTEM_PROMPT = """Du bist ein hilfreicher Assistent in einem interaktiven Werbesystem. Du hilfst dem Nutzer dabei:
1. Potenzielle Kunden zu finden (Websuche)
2. Firmen zu analysieren (Website crawlen, Steckbrief erstellen)
3. Passende Angebote zu identifizieren (Matching)
4. Personalisierte Kontaktanfragen zu erstellen (Email, Landing Page, Telefonskript)

Wichtige Regeln:
- Sei proaktiv und schlage immer naechste Schritte vor
- Frage IMMER nach Bestaetigung bevor du zur naechsten Phase wechselst
- Biete dem Nutzer Optionen an ("Ich kann A, B oder C machen. Was moechtest du?")
- Zeige immer an, in welcher Phase sich die Konversation befindet
- Antworte auf Deutsch

Aktuelle Phase: {phase}"""


async def respond_node(state: AgentState) -> dict:
    """Generate a response using the agent LLM."""
    llm = get_agent_llm()
    phase = state.get("current_phase", "search")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(phase=phase)),
        *state["messages"],
    ]

    response = await llm.ainvoke(messages)
    return {"messages": [response]}


async def respond_stream(state: AgentState):
    """Generate a streaming response using the agent LLM."""
    llm = get_agent_llm()
    phase = state.get("current_phase", "search")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(phase=phase)),
        *state["messages"],
    ]

    async for chunk in llm.astream(messages):
        yield chunk


def route_intent(state: AgentState) -> str:
    """Route to the appropriate node based on intent."""
    intent = state.get("intent", "general_chat")

    if intent == "search":
        return "search"
    elif intent == "crawl_url":
        return "crawler"
    else:
        return "respond"


def build_graph():
    """Build the LangGraph agent graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("respond", respond_node)
    graph.add_node("search", search_node)
    graph.add_node("crawler", crawler_node)

    # Set entry point
    graph.set_entry_point("router")

    # Add conditional edges from router
    graph.add_conditional_edges("router", route_intent, {
        "respond": "respond",
        "search": "search",
        "crawler": "crawler",
    })

    # All terminal nodes go to END
    graph.add_edge("respond", END)
    graph.add_edge("search", END)
    graph.add_edge("crawler", END)

    return graph


def compile_graph(checkpointer=None):
    """Compile the graph with optional checkpointer."""
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)


async def get_checkpointer():
    """Get an async SQLite checkpointer."""
    checkpointer = AsyncSqliteSaver.from_conn_string("./data/checkpoints.db")
    return checkpointer
