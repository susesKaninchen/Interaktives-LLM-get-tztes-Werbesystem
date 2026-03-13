"""Knowledge base CRUD endpoints."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import KnowledgeEntry
from app.db.vector_store import get_knowledge_collection

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class KnowledgeCreate(BaseModel):
    content: str
    tags: list[str] = []
    source_conversation_id: int | None = None


class KnowledgeResponse(BaseModel):
    id: int
    content: str
    tags: list[str] = []
    source_conversation_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[KnowledgeResponse])
async def list_knowledge(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeEntry).order_by(KnowledgeEntry.created_at.desc()))
    entries = result.scalars().all()
    return [
        KnowledgeResponse(
            id=e.id,
            content=e.content,
            tags=json.loads(e.tags_json) if e.tags_json else [],
            source_conversation_id=e.source_conversation_id,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.post("", response_model=KnowledgeResponse, status_code=201)
async def create_knowledge(data: KnowledgeCreate, db: AsyncSession = Depends(get_db)):
    entry = KnowledgeEntry(
        content=data.content,
        tags_json=json.dumps(data.tags, ensure_ascii=False) if data.tags else None,
        source_conversation_id=data.source_conversation_id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    # Also store in ChromaDB for semantic search
    collection = get_knowledge_collection()
    collection.upsert(
        ids=[f"knowledge_{entry.id}"],
        documents=[entry.content],
        metadatas=[{"tags": ",".join(data.tags), "source_conversation_id": str(data.source_conversation_id or "")}],
    )

    return KnowledgeResponse(
        id=entry.id,
        content=entry.content,
        tags=data.tags,
        source_conversation_id=entry.source_conversation_id,
        created_at=entry.created_at,
    )


@router.delete("/{entry_id}", status_code=204)
async def delete_knowledge(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await db.get(KnowledgeEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    # Remove from ChromaDB
    collection = get_knowledge_collection()
    try:
        collection.delete(ids=[f"knowledge_{entry_id}"])
    except Exception:
        pass

    await db.delete(entry)
    await db.commit()
