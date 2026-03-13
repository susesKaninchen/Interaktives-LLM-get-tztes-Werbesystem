"""Agent state definition for LangGraph."""

from typing import Annotated
from operator import add

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """State passed through the LangGraph agent graph."""
    messages: Annotated[list, add_messages]
    conversation_id: int
    current_phase: str
    intent: str  # Classified intent from router
    search_results: list[dict]  # Web search results
    selected_company: dict | None  # Selected company from search results
    company_profile: dict | None  # Built company profile
    user_profile: dict | None  # User's own profile
    matching_results: list[dict]  # Matching suggestions
    generated_content: str  # Generated outreach content
