"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.engine import engine
from app.db.models import Base
from app.routers import chat, customers, knowledge, profile, templates, dynamic_flow
from app.security import SecurityMiddleware, cleanup_rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directory exists
    Path("./data").mkdir(exist_ok=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start background cleanup task for rate limiter
    import asyncio
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Cleanup
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    await engine.dispose()


async def periodic_cleanup():
    """Periodically cleanup rate limiter entries."""
    import asyncio
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            await cleanup_rate_limiter()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")


app = FastAPI(
    title="Interaktives Werbesystem",
    version="0.2.0",
    lifespan=lifespan,
)

# Security middleware
app.add_middleware(SecurityMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(chat.router)
app.include_router(profile.router)
app.include_router(templates.router)
app.include_router(knowledge.router)
app.include_router(dynamic_flow.router, prefix="/api/dynamic")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/api/config/models")
async def get_models():
    from app.config import config
    return {
        "models": {k: {"model_name": v.model_name} for k, v in config.llm.models.items()},
        "routing": config.llm.routing.model_dump(),
    }
