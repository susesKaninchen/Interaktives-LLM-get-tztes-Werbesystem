"""Pydantic schemas for conversations and messages."""

from datetime import datetime

from pydantic import BaseModel


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    metadata_json: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    title: str = "Neue Konversation"


class ConversationResponse(BaseModel):
    id: int
    title: str
    status: str
    current_phase: str
    # company_profile accessed via relationship, not stored as column anymore
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationUpdate(BaseModel):
    title: str | None = None
    status: str | None = None


class ChatMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "message", "stream_start", "stream_token", "stream_end", "error"
    content: str = ""
    conversation_id: int | None = None
    phase: str | None = None
