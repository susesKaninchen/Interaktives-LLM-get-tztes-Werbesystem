"""WebSocket chat endpoint with LLM streaming via LangGraph."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select

from app.db.engine import async_session
from app.db.models import Conversation, Message
from app.agents.orchestrator import compile_graph, respond_stream
from app.agents.nodes.router import router_node

logger = logging.getLogger(__name__)
router = APIRouter()


async def load_chat_history(conversation_id: int) -> list:
    """Load existing messages as LangChain message objects."""
    chat_history = []
    async with async_session() as db:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        for msg in result.scalars().all():
            if msg.role == "user":
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                chat_history.append(AIMessage(content=msg.content))
    return chat_history


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

    chat_history = await load_chat_history(conversation_id)

    # Accumulated state across turns
    search_results = []
    selected_company = None

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

            chat_history.append(HumanMessage(content=user_content))

            # Build state for the graph
            state = {
                "messages": chat_history,
                "conversation_id": conversation_id,
                "current_phase": current_phase,
                "intent": "",
                "search_results": search_results,
                "selected_company": selected_company,
                "company_profile": None,
                "user_profile": None,
                "matching_results": [],
                "generated_content": "",
            }

            # Run intent classification
            try:
                intent_result = await router_node(state)
                intent = intent_result.get("intent", "general_chat")
                state["intent"] = intent
                logger.info(f"Intent classified: {intent}")
            except Exception as e:
                logger.warning(f"Router failed: {e}")
                intent = "general_chat"
                state["intent"] = intent

            await websocket.send_json({"type": "stream_start", "content": ""})

            full_content = ""

            # For search and crawl intents, run the graph (non-streaming)
            if intent in ("search", "crawl_url"):
                try:
                    graph = compile_graph()
                    result = await graph.ainvoke(state)

                    # Extract the last AI message
                    if result.get("messages"):
                        last_msg = result["messages"][-1]
                        full_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

                    # Update accumulated state
                    if result.get("search_results"):
                        search_results = result["search_results"]
                    if result.get("selected_company"):
                        selected_company = result["selected_company"]
                    if result.get("current_phase"):
                        current_phase = result["current_phase"]
                        # Update phase in DB
                        async with async_session() as db:
                            conv = await db.get(Conversation, conversation_id)
                            if conv:
                                from app.db.models import ConversationPhase
                                conv.current_phase = ConversationPhase(current_phase)
                                await db.commit()

                    await websocket.send_json({"type": "stream_token", "content": full_content})

                except Exception as e:
                    logger.error(f"Graph execution error: {e}")
                    full_content = f"Es gab einen Fehler: {e}"
                    await websocket.send_json({"type": "stream_token", "content": full_content})
            else:
                # For general chat: stream tokens directly
                try:
                    async for chunk in respond_stream(state):
                        token = chunk.content if hasattr(chunk, "content") else str(chunk)
                        if token:
                            full_content += token
                            await websocket.send_json({"type": "stream_token", "content": token})
                except Exception as e:
                    logger.error(f"LLM streaming error: {e}")
                    full_content = f"Entschuldigung, es gab einen Fehler: {e}"
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

            chat_history.append(AIMessage(content=full_content))

            await websocket.send_json({
                "type": "stream_end",
                "content": full_content,
                "phase": current_phase,
            })

    except WebSocketDisconnect:
        pass
