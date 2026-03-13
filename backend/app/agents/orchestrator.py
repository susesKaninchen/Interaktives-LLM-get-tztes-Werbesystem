"""LangGraph orchestrator - main agent graph."""

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.agents.state import AgentState
from app.agents.nodes.router import router_node
from app.agents.nodes.search import search_node
from app.agents.nodes.crawler import crawler_node
from app.agents.nodes.profile_builder import profile_builder_node
from app.agents.nodes.user_profile import user_profile_node
from app.agents.nodes.matching import matching_node
from app.agents.nodes.outreach import outreach_node
from app.agents.nodes.template_mgr import template_mgr_node
from app.agents.nodes.knowledge import knowledge_node
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

Aktuelle Phase: {phase}

{knowledge_section}"""


async def _build_system_prompt(phase: str) -> str:
    """Build system prompt with injected knowledge."""
    knowledge_section = ""
    try:
        from app.agents.nodes.knowledge import get_all_knowledge
        entries = await get_all_knowledge()
        if entries:
            items = "\n".join(f"- {e['content']}" for e in entries[:10])
            knowledge_section = f"Gespeichertes Wissen (nutze es als Kontext):\n{items}"
    except Exception:
        pass
    return SYSTEM_PROMPT.format(phase=phase, knowledge_section=knowledge_section)


async def respond_node(state: AgentState) -> dict:
    """Generate a response using the agent LLM."""
    llm = get_agent_llm()
    phase = state.get("current_phase", "search")
    system_prompt = await _build_system_prompt(phase)

    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"],
    ]

    response = await llm.ainvoke(messages)
    return {"messages": [response]}


async def respond_stream(state: AgentState):
    """Generate a streaming response using the agent LLM."""
    llm = get_agent_llm()
    phase = state.get("current_phase", "search")
    system_prompt = await _build_system_prompt(phase)

    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"],
    ]

    async for chunk in llm.astream(messages):
        yield chunk


def route_intent(state: AgentState) -> str:
    """Route to the appropriate node based on intent."""
    intent = state.get("intent", "general_chat")

    routing_map = {
        "search": "search",
        "crawl_url": "crawler",
        "matching": "matching",
        "outreach": "outreach",
        "user_profile": "user_profile",
        "template": "template_mgr",
        "knowledge": "knowledge",
    }

    # If matching is requested but we're still in profile phase, build profile first
    if intent == "matching" and state.get("current_phase") == "profile":
        return "profile_builder"

    return routing_map.get(intent, "respond")


def build_graph():
    """Build the LangGraph agent graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("respond", respond_node)
    graph.add_node("search", search_node)
    graph.add_node("crawler", crawler_node)
    graph.add_node("profile_builder", profile_builder_node)
    graph.add_node("user_profile", user_profile_node)
    graph.add_node("matching", matching_node)
    graph.add_node("outreach", outreach_node)
    graph.add_node("template_mgr", template_mgr_node)
    graph.add_node("knowledge", knowledge_node)

    # Set entry point
    graph.set_entry_point("router")

    # Add conditional edges from router
    graph.add_conditional_edges("router", route_intent, {
        "respond": "respond",
        "search": "search",
        "crawler": "crawler",
        "profile_builder": "profile_builder",
        "user_profile": "user_profile",
        "matching": "matching",
        "outreach": "outreach",
        "template_mgr": "template_mgr",
        "knowledge": "knowledge",
    })

    # All terminal nodes go to END
    graph.add_edge("respond", END)
    graph.add_edge("search", END)
    graph.add_edge("crawler", END)
    graph.add_edge("profile_builder", END)
    graph.add_edge("user_profile", END)
    graph.add_edge("matching", END)
    graph.add_edge("outreach", END)
    graph.add_edge("template_mgr", END)
    graph.add_edge("knowledge", END)

    return graph


def compile_graph(checkpointer=None):
    """Compile the graph with optional checkpointer."""
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)


async def get_checkpointer():
    """Get an async SQLite checkpointer."""
    checkpointer = AsyncSqliteSaver.from_conn_string("./data/checkpoints.db")
    return checkpointer
