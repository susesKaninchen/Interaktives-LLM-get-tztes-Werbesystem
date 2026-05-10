"""WebSocket chat endpoint with LLM streaming via LangGraph and dynamic flow."""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select

from app.db.engine import async_session
from app.db.models import Conversation, ConversationPhase, Message
from app.agents.orchestrator import compile_graph, respond_stream
from app.agents.nodes.router import router_node
from app.agents.conversation_state import get_state_manager, ConversationState
from app.agents.conversation_controller import get_conversation_controller

logger = logging.getLogger(__name__)
router = APIRouter()

INTENT_LABELS = {
    "search": "Suche im Web...",
    "crawl_url": "Crawle Website...",
    "matching": "Erstelle Matching...",
    "outreach": "Generiere Kontaktanfrage...",
    "user_profile": "Aktualisiere Profil...",
    "template": "Verwalte Vorlagen...",
    "knowledge": "Verarbeite Wissen...",
    "general_chat": "Denke nach...",
}


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


async def send_status(ws: WebSocket, text: str):
    """Send a status update to the frontend."""
    await ws.send_json({"type": "status", "content": text})


async def send_error(ws: WebSocket, text: str, details: Optional[dict] = None):
    """Send an error message to the frontend."""
    error_data = {"type": "error", "content": text}
    if details:
        error_data["details"] = details
    await ws.send_json(error_data)


async def send_progress(ws: WebSocket, current: int, total: int, message: str):
    """Send progress update to the frontend."""
    await ws.send_json({
        "type": "progress",
        "current": current,
        "total": total,
        "message": message
    })


@router.websocket("/ws/chat/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: int):
    """WebSocket chat endpoint with improved state management and error handling."""
    
    await websocket.accept()
    
    # Initialize state manager and load state
    state_manager = get_state_manager()
    conv_state = await state_manager.load_state(conversation_id)
    
    # Verify conversation exists
    async with async_session() as db:
        conv = await db.get(Conversation, conversation_id)
        if not conv:
            await send_error(websocket, "Conversation not found")
            await websocket.close()
            return
    
    # Load chat history
    chat_history = await load_chat_history(conversation_id)
    
    # Heartbeat tracking
    last_heartbeat = asyncio.get_event_loop().time()
    HEARTBEAT_INTERVAL = 30  # seconds
    HEARTBEAT_TIMEOUT = 60   # seconds

    async def send_heartbeat():
        """Send periodic heartbeat messages."""
        nonlocal last_heartbeat
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                current_time = asyncio.get_event_loop().time()
                if current_time - last_heartbeat > HEARTBEAT_TIMEOUT:
                    logger.warning(f"Heartbeat timeout for conversation {conversation_id}")
                    break
                
                await websocket.send_json({"type": "heartbeat", "timestamp": current_time})
                last_heartbeat = current_time
            except Exception as e:
                logger.warning(f"Heartbeat failed: {e}")
                break
    
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(send_heartbeat())

    async def execute_with_retry(func, max_retries=3, delay=1):
        """Execute a function with retry logic."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff
        raise last_error

    try:
        while True:
            # Update heartbeat on receive
            last_heartbeat = asyncio.get_event_loop().time()
            
            data = await websocket.receive_json()
            
            # Handle heartbeat response
            if data.get("type") == "heartbeat_ack":
                continue
            
            user_content = data.get("content", "").strip()
            if not user_content:
                await send_error(websocket, "Empty message content")
                continue

            # Input validation
            if len(user_content) > 10000:
                await send_error(websocket, "Message too long (max 10000 characters)")
                continue

            # Save user message
            try:
                async with async_session() as db:
                    user_msg = Message(
                        conversation_id=conversation_id,
                        role="user",
                        content=user_content,
                    )
                    db.add(user_msg)
                    await db.commit()
            except Exception as e:
                logger.error(f"Failed to save user message: {e}")
                await send_error(websocket, "Failed to save message")
                continue

            chat_history.append(HumanMessage(content=user_content))

            # Build state for the graph
            agent_state = {
                "messages": chat_history,
                "conversation_id": conversation_id,
                "current_phase": conv_state.current_phase,
                "intent": "",
                "search_results": conv_state.search_results,
                "selected_company": conv_state.selected_company,
                "company_profile": conv_state.company_profile,
                "user_profile": conv_state.user_profile,
                "matching_results": conv_state.matching_results,
                "generated_content": conv_state.generated_content,
            }

            # --- Intent classification ---
            await send_status(websocket, "Analysiere Nachricht...")
            
            intent = "general_chat"
            try:
                intent_result = await execute_with_retry(
                    lambda: router_node(agent_state),
                    max_retries=2
                )
                intent = intent_result.get("intent", "general_chat")
                logger.info(f"Intent classified: {intent}")
                
                # Update state with new intent
                conv_state = conv_state.with_intent(intent)
                await state_manager.save_state(conv_state)
                
            except asyncio.TimeoutError:
                logger.warning(f"Router timed out for conversation {conversation_id}")
                await send_error(websocket, "Analysierung dauerte zu lange, bitte versuche es erneut")
                continue
            except Exception as e:
                logger.error(f"Router failed for conversation {conversation_id}: {e}", exc_info=True)
                await send_error(websocket, f"Fehler bei der Analysierung: {str(e)}")
                continue

            # --- Intent validation ---
            # Check if intent is valid for current state
            if intent in ("matching", "outreach") and not conv_state.can_proceed_to_matching():
                await send_status(websocket, "Validiere Vorbedingungen...")
                await send_error(
                    websocket, 
                    "Du benötigst zuerst Firmen- und Benutzerdaten für diese Funktion. Bitte durchsuche zuerst nach Firmen und erstelle dann dein Profil.",
                    {"required_phase": "profile", "current_phase": conv_state.current_phase}
                )
                continue

            # --- Execute intent ---
            await send_status(websocket, INTENT_LABELS.get(intent, "Verarbeite..."))
            await websocket.send_json({"type": "stream_start", "content": ""})

            full_content = ""

            try:
                if intent in ("search", "crawl_url", "matching", "user_profile", "outreach", "template", "knowledge"):
                    # Send progress for tool-based operations
                    if intent == "crawl_url":
                        await send_progress(websocket, 1, 3, "Initialisiere Crawler...")
                    
                    graph = compile_graph()
                    result = await execute_with_retry(
                        lambda: graph.ainvoke(agent_state),
                        max_retries=2
                    )

                    # Extract the last AI message
                    if result.get("messages"):
                        last_msg = result["messages"][-1]
                        full_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

                    # Update state with results
                    state_updates = {}
                    
                    if result.get("search_results"):
                        state_updates["search_results"] = result["search_results"]
                    if result.get("selected_company"):
                        state_updates["selected_company"] = result["selected_company"]
                    if result.get("company_profile"):
                        state_updates["company_profile"] = result["company_profile"]
                    if result.get("user_profile"):
                        state_updates["user_profile"] = result["user_profile"]
                    if result.get("matching_results"):
                        state_updates["matching_results"] = result["matching_results"]
                    if result.get("generated_content"):
                        state_updates["generated_content"] = result["generated_content"]
                    if result.get("current_phase"):
                        state_updates["current_phase"] = result["current_phase"]
                        
                        # Update database phase
                        async with async_session() as db:
                            conv = await db.get(Conversation, conversation_id)
                            if conv:
                                conv.current_phase = ConversationPhase(result["current_phase"])
                                await db.commit()
                    
                    # Apply state updates
                    if state_updates:
                        conv_state = conv_state.update(**state_updates)
                        await state_manager.save_state(conv_state)

                    await websocket.send_json({"type": "stream_token", "content": full_content})
                    
                else:
                    # For general chat: stream tokens directly
                    await send_status(websocket, "Generiere Antwort...")
                    
                    async for chunk in respond_stream(agent_state):
                        token = chunk.content if hasattr(chunk, "content") else str(chunk)
                        if token:
                            full_content += token
                            await websocket.send_json({"type": "stream_token", "content": token})

            except asyncio.TimeoutError:
                logger.error(f"Execution timeout for conversation {conversation_id}")
                full_content = "Die Operation dauerte zu lange. Bitte versuche es erneut mit einer kürzeren Anfrage."
                await websocket.send_json({"type": "stream_token", "content": full_content})
                
            except Exception as e:
                logger.error(f"Execution error for conversation {conversation_id}: {e}", exc_info=True)
                error_message = f"Leider gab es einen Fehler bei der Verarbeitung: {str(e)}"
                full_content = error_message
                await websocket.send_json({"type": "stream_token", "content": error_message})

            # Save assistant message
            try:
                async with async_session() as db:
                    assistant_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_content,
                    )
                    db.add(assistant_msg)
                    await db.commit()
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")

            chat_history.append(AIMessage(content=full_content))

            await websocket.send_json({
                "type": "stream_end",
                "content": full_content,
                "phase": conv_state.current_phase,
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.exception(f"Unexpected error in WebSocket handler for conversation {conversation_id}: {e}")
        try:
            await send_error(websocket, f"Unerwarteter Fehler: {str(e)}")
        except Exception:
            pass
    finally:
        # Cleanup
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        
        # Save final state
        try:
            await state_manager.save_state(conv_state)
        except Exception as e:
            logger.error(f"Failed to save final state: {e}")
