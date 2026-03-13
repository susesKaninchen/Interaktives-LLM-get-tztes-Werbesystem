"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.engine import engine
from app.db.models import Base
from app.routers import chat, customers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directory exists
    Path("./data").mkdir(exist_ok=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title="Interaktives Werbesystem",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(chat.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
