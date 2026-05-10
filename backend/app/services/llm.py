"""LLM client factory using OpenAI-compatible API."""

from langchain_openai import ChatOpenAI

from app.config import config
from app.performance import cache_response, monitor_performance


def get_llm(model_key: str | None = None) -> ChatOpenAI:
    """Create a ChatOpenAI instance for the given model key."""
    if model_key is None:
        model_key = config.llm.default_model

    model_config = config.llm.models[model_key]

    return ChatOpenAI(
        base_url=model_config.base_url,
        api_key=model_config.api_key,
        model=model_config.model_name,
        temperature=model_config.temperature,
        max_tokens=model_config.max_tokens,
    )


def get_router_llm() -> ChatOpenAI:
    """LLM for intent classification (fast model)."""
    return get_llm(config.llm.routing.router)


def get_agent_llm() -> ChatOpenAI:
    """LLM for content generation (smart model)."""
    return get_llm(config.llm.routing.agents)


# Cached versions for frequently used prompts
def get_cached_router_llm() -> ChatOpenAI:
    """Get cached LLM instance for router."""
    return get_router_llm()


def get_cached_agent_llm() -> ChatOpenAI:
    """Get cached LLM instance for agent."""
    return get_agent_llm()
