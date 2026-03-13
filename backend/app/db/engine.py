"""Async SQLite engine and session factory."""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import config

# Ensure data directory exists
data_dir = Path("./data")
data_dir.mkdir(exist_ok=True)

engine = create_async_engine(config.database.sqlite_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Dependency for FastAPI routes."""
    async with async_session() as session:
        yield session
