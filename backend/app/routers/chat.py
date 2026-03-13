"""WebSocket chat endpoint with echo mode for Phase 1."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session
from app.db.models import Conversation, Message

router = APIRouter()


@router.websocket("/ws/chat/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: int):
    await websocket.accept()

    async with async_session() as db:
        conv = await db.get(Conversation, conversation_id)
        if not conv:
            await websocket.send_json({"type": "error", "content": "Conversation not found"})
            await websocket.close()
            return

    try:
        while True:
            data = await websocket.receive_json()
            user_content = data.get("content", "")

            async with async_session() as db:
                # Save user message
                user_msg = Message(
                    conversation_id=conversation_id,
                    role="user",
                    content=user_content,
                )
                db.add(user_msg)
                await db.commit()

                # Echo mode for Phase 1 - will be replaced with LLM in Phase 2
                echo_content = f"Echo: {user_content}"

                # Save assistant message
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=echo_content,
                )
                db.add(assistant_msg)
                await db.commit()

            # Send response
            await websocket.send_json({
                "type": "stream_start",
                "content": "",
            })
            await websocket.send_json({
                "type": "stream_token",
                "content": echo_content,
            })
            await websocket.send_json({
                "type": "stream_end",
                "content": echo_content,
                "phase": "search",
            })

    except WebSocketDisconnect:
        pass
