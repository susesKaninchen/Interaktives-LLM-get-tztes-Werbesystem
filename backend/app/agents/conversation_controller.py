"""AI-driven conversation controller for dynamic dialog management."""

import logging
from typing import Optional, List, Dict, Any
from langchain_core.messages import SystemMessage, AIMessage

from app.agents.dynamic_flow import DynamicFlowEngine, FlowState, FlowAction, get_flow_engine
from app.services.llm import get_agent_llm

logger = logging.getLogger(__name__)


class ConversationController:
    """Controller for AI-driven conversation management."""
    
    def __init__(self):
        """Initialize the conversation controller."""
        self.flow_engine = DynamicFlowEngine()
        self.llm = get_agent_llm()
        self.conversation_context: Dict[str, Any] = {}
        self.user_preferences: Dict[str, Any] = {}
        self.suggestion_history: List[Dict[str, Any]] = []
    
    def initialize_conversation(self, goals: List[str] = None, preferences: Dict[str, Any] = None) -> str:
        """Initialize a new dynamic conversation."""
        # Initialize flow
        self.flow_engine.initialize_flow(goals)
        self.user_preferences = preferences or {}
        
        # Generate welcome message
        welcome_message = self._generate_welcome_message()
        
        return welcome_message
    
    def process_user_message(self, message: str, current_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user message and generate intelligent response."""
        # Update context
        if current_context:
            self.conversation_context.update(current_context)
        
        # Analyze user intent with flow engine
        flow_response = self.flow_engine.handle_user_intent(message, current_context)
        
        # Generate AI response based on flow state
        ai_response = self._generate_ai_response(message, flow_response)
        
        # Get AI suggestions for next steps
        suggestions = self._get_intelligent_suggestions()
        
        return {
            "ai_response": ai_response,
            "flow_suggestions": suggestions,
            "available_actions": self._get_available_actions(),
            "current_step": self.flow_engine.current_state.current_step if self.flow_engine.current_state else None,
            "conversation_progress": self._get_conversation_progress()
        }
    
    def _generate_welcome_message(self) -> str:
        """Generate personalized welcome message."""
        flow_summary = self.flow_engine.get_flow_summary()
        current_step = flow_summary.get("current_step", "initialization")
        
        if self.user_preferences.get("experience_level") == "advanced":
            return """👋 Hallo! Willkommen zurück! 

Ich sehe du hast Erfahrung mit dem System. Du kannst jederzeit andere Wege gehen, Schritte überspringen oder zu früheren Punkten zurückkehren.

Was möchtest du heute anpacken? Ich kann folgende Optionen vorschlagen:

🎯 **Direkter Start:** Kunde suchen → Analysieren → Kontaktieren
🔄 **Iterativer Prozess:** schrittweise mit Feedback-Schleifen
⚡ **Schnellweg:** Direkt zum Matching mit vorhandenem Profil

Oder sag mir einfach, was dein Ziel ist, und ich passe den Ablauf entsprechend an!"""
        else:
            return """👋 Willkommen! Ich bin dein KI-Assistent für das Werbesystem.

Ich helfe dir dabei, die richtigen Kunden zu finden und personalisierte Angebote zu erstellen. Dabei können wir ganz flexibel vorgehen:

🎯 **Wir starten gemeinsam** - ich schlage Schritte vor, du entscheidest
💬 **Natürliche Konversation** - sag einfach, was du erreichen möchtest
🔄 **Kein starrer Weg** - wir können jederzeit umsteigen oder zurückgehen

Worauf möchtest du dich heute konzentrieren? Egal ob Kundensuche, Angebotserstellung oder was ganz anderes - ich passe mich an!"""
    
    def _generate_ai_response(self, user_message: str, flow_response: Dict[str, Any]) -> str:
        """Generate AI response based on user message and flow state."""
        current_context = self._build_ai_context()
        
        # Build system prompt with dynamic flow awareness
        system_prompt = self._build_dynamic_system_prompt(current_context)
        
        # Generate response using LLM
        try:
            messages = [
                SystemMessage(content=system_prompt),
                *[self._context_to_message(msg) for msg in self._get_conversation_history()],
            ]
            
            response = self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return self._get_fallback_response(user_message, flow_response)
    
    def _build_ai_context(self) -> Dict[str, Any]:
        """Build context for AI decision making."""
        flow_summary = self.flow_engine.get_flow_summary()
        
        return {
            "current_step": flow_summary.get("current_step"),
            "completed_steps": flow_summary.get("completed_steps", []),
            "progress": flow_summary.get("progress", 0.0),
            "available_actions": [t.action.value for t in self.flow_engine.current_state.available_transitions] if self.flow_engine.current_state else [],
            "user_experience": self.user_preferences.get("experience_level", "beginner"),
            "conversation_goals": self.flow_engine.flow_goals,
            "user_message_count": len(self.suggestion_history),
            "recent_actions": self.suggestion_history[-3:] if self.suggestion_history else []
        }
    
    def _build_dynamic_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt that adapts to dynamic flow."""
        current_step = context.get("current_step", "initialization")
        progress = context.get("progress", 0.0)
        experience = context.get("user_experience", "beginner")
        
        prompt = f"""Du bist ein intelligenter Assistent für ein interaktives Werbesystem. Deine Aufgabe ist es, natürliche Konversationen zu führen und dem Nutzer optimale下一 Schritte vorzuschlagen.

**Aktueller Status:**
- Phase: {current_step}
- Fortschritt: {progress:.0%}
- Erfahrungsniveau des Nutzers: {experience}

**Deine Prinzipien:**
1. **Sei adaptiv** - Passe dich dem Nutzerverhalten und den Zielen an
2. **Gib Optionen** - Biete immer verschiedene next steps an, nicht nur einen starren Weg
3. **Sei proaktiv** - Schlage intelligente Verbesserungen vor basierend auf Kontext
4. **Erkenne Absichten** - Wenn der Nutzer etwas Bestimmtes will, unterbrich den normalen Flow
5. **Biete Flexibilität** - Schlüge Überspringen, Zurückgehen oder Iterieren an wo sinnvoll

**Aktuelle Möglichkeiten:**
- Verfügbare Aktionen: {', '.join(context.get('available_actions', []))}
- Abgeschlossene Schritte: {', '.join(context.get('completed_steps', [])) if context.get('completed_steps') else 'Keine'}

**Antwort-Richtlinien:**
- Beginne immer mit einer direkten Antwort auf die Nutzerwunsch
- Schlág dann 2-3 next steps vor mit kurzer Begründung
- Biete an, Schritte zu überspringen oder zu wiederholen wo sinnvoll
- Sei natürlich und konversativ, nicht robotisch
- Erkenne wenn der Nutzer seinen eigenen Weg gehen möchte

**Beispiel für adaptive Antworten:**
- Anstatt: "Jetzt müssen wir Schritt 2 machen."
- Sag: "Das ist ein guter Ansatz! Wir können damit fortfahren, oder wenn du lieber bei Schritt 1 etwas ändern möchtest, können wir das auch tun."""
        
        # Add experience-specific instructions
        if experience == "advanced":
            prompt += """

**Für erfahrene Nutzer:**
- Sei direkter und technischer
- Biete fortgeschrittene Optionen an
- Gib weniger Erklärungen, mehr Action-Items"""
        else:
            prompt += """

** für weniger erfahrene Nutzer:**
- Sei erklärungsbereit
- Schlág einfachere Wege vor
- Biete mehr Hilfestellung an"""
        
        return prompt
    
    def _get_intelligent_suggestions(self) -> List[Dict[str, Any]]:
        """Get intelligent suggestions for next steps."""
        ai_suggestions = self.flow_engine.ai_suggest_next_step()
        
        if not ai_suggestions:
            return []
        
        # Store suggestion history
        self.suggestion_history.append({
            "timestamp": self._current_timestamp(),
            "suggestions": ai_suggestions
        })
        
        # Customize suggestions based on user preferences
        customized = []
        for suggestion in ai_suggestions.get("suggestions", []):
            customized_suggestion = self._customize_suggestion(suggestion)
            customized.append(customized_suggestion)
        
        return customized
    
    def _customize_suggestion(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """Customize suggestion based on user preferences."""
        custom = suggestion.copy()
        
        # Adjust confidence based on user preferences
        if custom["target_step"] in self.user_preferences.get("preferred_steps", []):
            custom["confidence"] = min(custom["confidence"] + 0.2, 1.0)
        
        # Add user-friendly reasoning
        if self.user_preferences.get("experience_level") == "beginner":
            custom["reasoning"] = self._add_explanation(custom["reasoning"])
        
        return custom
    
    def _add_explanation(self, reasoning: str) -> str:
        """Add beginner-friendly explanation."""
        explanations = {
            "forward": "Damit gehen wir einen logischen Schritt weiter",
            "iterate": "So können wir das Ergebnis verbessern",
            "skip": "Dies spart Zeit bei Dingen, die du schon kennst",
            "backward": "So können wir etwas ändern oder neu versuchen"
        }
        
        for key, explanation in explanations.items():
            if key in reasoning.lower():
                return f"{reasoning} ({explanation})"
        
        return reasoning
    
    def _get_available_actions(self) -> List[Dict[str, Any]]:
        """Get available actions for user."""
        if not self.flow_engine.current_state:
            return []
        
        actions = []
        for transition in self.flow_engine.current_state.available_transitions:
            action_info = {
                "type": transition.action.value,
                "target_step": transition.to_step,
                "user_friendly": self._get_user_friendly_action_name(transition.action.value, transition.to_step),
                "is_recommended": transition.ai_suggested
            }
            actions.append(action_info)
        
        return actions
    
    def _get_user_friendly_action_name(self, action: str, target_step: str) -> str:
        """Get user-friendly name for action."""
        step_names = {
            "discovery": "Ziele verstehen",
            "search": "Kunden suchen",
            "analysis": "Unternehmen analysieren",
            "profiling": "Profile erstellen",
            "matching": "Angebote matching",
            "outreach_preparation": "Kontakt vorbereiten",
            "outreach_execution": "Kunden kontaktieren"
        }
        
        target_name = step_names.get(target_step, target_step)
        
        action_prefixes = {
            "forward": "Weiter zu",
            "backward": "Zurück zu",
            "iterate": "Verfeinern:",
            "skip": "Überspringen zu",
            "modify": "Ändern: "
        }
        
        prefix = action_prefixes.get(action, "")
        return f"{prefix} {target_name}" if prefix else target_name
    
    def _get_conversation_progress(self) -> Dict[str, Any]:
        """Get overall conversation progress."""
        flow_summary = self.flow_engine.get_flow_summary()
        
        return {
            "percentage": flow_summary.get("progress", 0.0) * 100,
            "current_step": flow_summary.get("current_step"),
            "total_steps": len(self.flow_engine.flow_steps),
            "completed_steps": len(flow_summary.get("completed_steps", []))
        }
    
    def _get_fallback_response(self, user_message: str, flow_response: Dict[str, Any]) -> str:
        """Get fallback response when AI fails."""
        suggested_actions = flow_response.get("suggested_actions", [])
        
        if suggested_actions:
            action = suggested_actions[0]
            return f"Verstehe! Möchtest du {action.get('action')} {action.get('target_step', '')}? Ich kann dir dabei helfen oder wir können auch etwas anderes machen."
        
        return "Das habe ich verstanden. Wie möchtest du weitermachen? Ich kann dir verschiedene Optionen vorschlagen."
    
    def _get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history for context."""
        # This would be implemented with actual conversation history
        return []
    
    def _context_to_message(self, context_item: Dict[str, Any]) -> SystemMessage:
        """Convert context item to message."""
        return SystemMessage(content=str(context_item))
    
    def _current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def handle_flow_transition(self, action: str, target_step: str = None) -> bool:
        """Handle user-initiated flow transition."""
        try:
            flow_action = FlowAction(action)
            
            if target_step:
                return self.flow_engine.transition_to(target_step, flow_action)
            else:
                # Handle action without specific target step
                if flow_action == FlowAction.BACKWARD:
                    # Go back to last completed step
                    if self.flow_engine.current_state.completed_steps:
                        return self.flow_engine.transition_to(
                            self.flow_engine.current_state.completed_steps[-1],
                            flow_action
                        )
                elif flow_action == FlowAction.FORWARD:
                    # Go to next logical step
                    next_step = self.flow_engine._get_next_step()
                    if next_step:
                        return self.flow_engine.transition_to(next_step, flow_action)
                elif flow_action == FlowAction.ITERATE:
                    # Iterate on current step
                    return self.flow_engine.transition_to(
                        self.flow_engine.current_state.current_step,
                        flow_action
                    )
            
            return False
        except ValueError:
            logger.error(f"Invalid flow action: {action}")
            return False


# Global conversation controller instance
_conversation_controller: Optional[ConversationController] = None


def get_conversation_controller() -> ConversationController:
    """Get global conversation controller instance."""
    global _conversation_controller
    if _conversation_controller is None:
        _conversation_controller = ConversationController()
    return _conversation_controller