"""Application configuration loaded from config.yaml."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class LLMModelConfig(BaseModel):
    base_url: str
    api_key: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 4096
    description: str = ""


class LLMRoutingConfig(BaseModel):
    router: str = "oss-120b"
    agents: str = "qwen-27b"
    embedding: str = "local"


class LLMConfig(BaseModel):
    default_model: str = "oss-120b"
    models: dict[str, LLMModelConfig] = {}
    routing: LLMRoutingConfig = LLMRoutingConfig()


class DatabaseConfig(BaseModel):
    sqlite_url: str = "sqlite+aiosqlite:///./data/app.db"
    chroma_persist_dir: str = "./data/chroma"


class SearchConfig(BaseModel):
    provider: str = "duckduckgo"


class CrawlerConfig(BaseModel):
    max_pages: int = 10
    timeout_seconds: int = 30


class AppConfig(BaseModel):
    llm: LLMConfig = LLMConfig()
    database: DatabaseConfig = DatabaseConfig()
    search: SearchConfig = SearchConfig()
    crawler: CrawlerConfig = CrawlerConfig()


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load configuration from config.yaml."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
    config_path = Path(config_path)

    if config_path.exists():
        with open(config_path) as f:
            raw: dict[str, Any] = yaml.safe_load(f) or {}
        return AppConfig(**raw)

    return AppConfig()


config = load_config()
