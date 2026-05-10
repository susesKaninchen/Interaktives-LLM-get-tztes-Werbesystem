"""API router for dynamic flow management and conversation control."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.agents.conversation_controller import get_conversation_controller

router = APIRouter()


class ConversationInitRequest(BaseModel):
    """Request to initialize a new dynamic conversation."""
    goals: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None
    experience_level: Optional[str] = "beginner"


class FlowActionRequest(BaseModel):
    """Request to perform a flow action."""
    action: str
    target_step: Optional[str] = None


class UserMessageRequest(BaseModel):
    """Request to process user message with dynamic flow."""
    message: str
    current_context: Optional[Dict[str, Any]] = None


@router.post("/conversation/init")
async def initialize_conversation(request: ConversationInitRequest) -> Dict[str, Any]:
    """Initialize a new dynamic conversation with flow engine."""
    try:
        controller = get_conversation_controller()
        
        # Set experience level in preferences
        preferences = request.preferences or {}
        if request.experience_level:
            preferences["experience_level"] = request.experience_level
        
        # Initialize conversation
        welcome_message = controller.initialize_conversation(request.goals, preferences)
        
        # Get initial flow state
        flow_summary = controller.flow_engine.get_flow_summary()
        initial_suggestions = controller._get_intelligent_suggestions()
        
        return {
            "welcome_message": welcome_message,
            "flow_state": flow_summary,
            "suggestions": initial_suggestions,
            "available_actions": controller._get_available_actions(),
            "conversation_progress": controller._get_conversation_progress()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize conversation: {str(e)}")


@router.post("/conversation/message")
async def process_user_message(request: UserMessageRequest) -> Dict[str, Any]:
    """Process user message with dynamic flow and AI suggestions."""
    try:
        controller = get_conversation_controller()
        
        # Process message through dynamic flow controller
        response = controller.process_user_message(
            request.message,
            request.current_context
        )
        
        return {
            "ai_response": response["ai_response"],
            "flow_suggestions": response["flow_suggestions"],
            "available_actions": response["available_actions"],
            "current_step": response["current_step"],
            "conversation_progress": response["conversation_progress"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.post("/flow/execute")
async def execute_flow_action(request: FlowActionRequest) -> Dict[str, Any]:
    """Execute a flow action (forward, backward, iterate, skip, etc.)."""
    try:
        controller = get_conversation_controller()
        
        # Execute the flow transition
        success = controller.handle_flow_transition(request.action, request.target_step)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to execute flow action: {request.action} -> {request.target_step}"
            )
        
        # Get updated flow state
        flow_summary = controller.flow_engine.get_flow_summary()
        new_suggestions = controller._get_intelligent_suggestions()
        
        # Generate transition message
        transition_message = controller._generate_transition_message(
            request.action, 
            request.target_step or controller.flow_engine.current_state.current_step
        )
        
        return {
            "success": True,
            "transition_message": transition_message,
            "flow_state": flow_summary,
            "suggestions": new_suggestions,
            "available_actions": controller._get_available_actions(),
            "conversation_progress": controller._get_conversation_progress()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute flow action: {str(e)}")


@router.get("/flow/state")
async def get_flow_state() -> Dict[str, Any]:
    """Get current flow state and available options."""
    try:
        controller = get_conversation_controller()
        
        return {
            "flow_state": controller.flow_engine.get_flow_summary(),
            "suggestions": controller._get_intelligent_suggestions(),
            "available_actions": controller._get_available_actions(),
            "conversation_progress": controller._get_conversation_progress(),
            "user_preferences": controller.user_preferences
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get flow state: {str(e)}")


@router.get("/flow/suggestions")
async def get_flow_suggestions() -> List[Dict[str, Any]]:
    """Get intelligent suggestions for next steps."""
    try:
        controller = get_conversation_controller()
        return controller._get_intelligent_suggestions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.post("/preferences/update")
async def update_preferences(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Update user preferences for the conversation."""
    try:
        controller = get_conversation_controller()
        controller.user_preferences.update(preferences)
        
        # Regenerate suggestions with new preferences
        new_suggestions = controller._get_intelligent_suggestions()
        
        return {
            "success": True,
            "preferences": controller.user_preferences,
            "updated_suggestions": new_suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


@router.get("/flow/history")
async def get_flow_history() -> List[Dict[str, Any]]:
    """Get history of flow transitions."""
    try:
        controller = get_conversation_controller()
        return controller.flow_engine.flow_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get flow history: {str(e)}")