"""WebSocket chat endpoint with LLM streaming."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage

from app.db.engine import async_session
from app.db.models import Conversation, Message
from app.agents.orchestrator import respond_stream
from app.agents.nodes.router import router_node

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/chat/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: int):
    await websocket.accept()

    # Verify conversation exists
    async with async_session() as db:
        conv = await db.get(Conversation, conversation_id)
        if not conv:
            await websocket.send_json({"type": "error", "content": "Conversation not found"})
            await websocket.close()
            return
        current_phase = conv.current_phase.value if conv.current_phase else "search"

    # Load existing messages for context
    chat_history = []
    async with async_session() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        for msg in result.scalars().all():
            if msg.role == "user":
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                from langchain_core.messages import AIMessage
                chat_history.append(AIMessage(content=msg.content))

    try:
        while True:
            data = await websocket.receive_json()
            user_content = data.get("content", "")

            # Save user message
            async with async_session() as db:
                user_msg = Message(
                    conversation_id=conversation_id,
                    role="user",
                    content=user_content,
                )
                db.add(user_msg)
                await db.commit()

            # Add to chat history
            chat_history.append(HumanMessage(content=user_content))

            # Build state for the agent
            state = {
                "messages": chat_history,
                "conversation_id": conversation_id,
                "current_phase": current_phase,
                "intent": "",
                "search_results": [],
                "selected_company": None,
                "company_profile": None,
                "user_profile": None,
                "matching_results": [],
                "generated_content": "",
            }

            # Classify intent (fire and forget for now, will be used in later phases)
            try:
                intent_result = await router_node(state)
                state["intent"] = intent_result.get("intent", "general_chat")
            except Exception as e:
                logger.warning(f"Router failed: {e}")
                state["intent"] = "general_chat"

            # Stream LLM response
            await websocket.send_json({"type": "stream_start", "content": ""})

            full_content = ""
            try:
                async for chunk in respond_stream(state):
                    token = chunk.content if hasattr(chunk, "content") else str(chunk)
                    if token:
                        full_content += token
                        await websocket.send_json({"type": "stream_token", "content": token})
            except Exception as e:
                logger.error(f"LLM streaming error: {e}")
                full_content = f"Entschuldigung, es gab einen Fehler bei der Verarbeitung: {e}"
                await websocket.send_json({"type": "stream_token", "content": full_content})

            # Save assistant message
            async with async_session() as db:
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_content,
                )
                db.add(assistant_msg)
                await db.commit()

            # Add to chat history
            from langchain_core.messages import AIMessage
            chat_history.append(AIMessage(content=full_content))

            await websocket.send_json({
                "type": "stream_end",
                "content": full_content,
                "phase": current_phase,
            })

    except WebSocketDisconnect:
        pass
