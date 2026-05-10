"""Dynamic flow engine for adaptive conversation management."""

import logging
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FlowAction(Enum):
    """Types of flow actions."""
    FORWARD = "forward"
    BACKWARD = "backward"
    SKIP = "skip"
    ITERATE = "iterate"
    BRANCH = "branch"
    MODIFY = "modify"
    PAUSE = "pause"
    RESUME = "resume"


@dataclass
class FlowState:
    """Current state of the conversation flow."""
    current_step: str
    completed_steps: List[str] = field(default_factory=list)
    available_transitions: List[FlowAction] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    user_intent: Optional[str] = None
    confidence: float = 0.0
    
    def can_proceed_to(self, target_step: str) -> bool:
        """Check if transition to target step is possible."""
        return target_step in self.available_transitions
    
    def mark_completed(self, step: str):
        """Mark a step as completed."""
        if step not in self.completed_steps:
            self.completed_steps.append(step)
    
    def is_completed(self, step: str) -> bool:
        """Check if step is completed."""
        return step in self.completed_steps


@dataclass
class FlowTransition:
    """Definition of a flow transition."""
    from_step: str
    to_step: str
    action: FlowAction
    condition: Optional[Callable[[FlowState], bool]] = None
    ai_suggested: bool = False
    confidence: float = 0.0


class DynamicFlowEngine:
    """Engine for managing dynamic conversation flows."""
    
    def __init__(self):
        """Initialize the dynamic flow engine."""
        self.flow_steps: Dict[str, Dict[str, Any]] = {}
        self.transitions: List[FlowTransition] = []
        self.current_state: Optional[FlowState] = None
        self.flow_history: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {}
        self.flow_goals: List[str] = []
        
        self._initialize_default_flow()
    
    def _initialize_default_flow(self):
        """Initialize the default conversation flow."""
        # Define flow steps with metadata
        self.flow_steps = {
            "initialization": {
                "name": "Initialisierung",
                "description": "Erste Schritte conversation setup",
                "required_data": [],
                "ai_driven": True,
                "skipable": False
            },
            "discovery": {
                "name": "Entdeckung",
                "description": "Kundenbedarf und Ziele verstehen",
                "required_data": [],
                "ai_driven": True,
                "skipable": True,
                "iterable": True
            },
            "search": {
                "name": "Suche",
                "description": "Nach potenziellen Kunden suchen",
                "required_data": ["discovery"],
                "ai_driven": True,
                "skipable": False,
                "iterable": True
            },
            "analysis": {
                "name": "Analyse",
                "description": "Gefundene Unternehmen analysieren",
                "required_data": ["search"],
                "ai_driven": True,
                "skipable": True,
                "iterable": True
            },
            "profiling": {
                "name": "Profilierung",
                "description": "Detaillierte Unternehmensprofile erstellen",
                "required_data": ["analysis"],
                "ai_driven": True,
                "skipable": True,
                "iterable": True
            },
            "matching": {
                "name": "Matching",
                "description": "Angebote passend zuordnen",
                "required_data": ["profiling", "user_profile"],
                "ai_driven": True,
                "skipable": False,
                "iterable": True
            },
            "outreach_preparation": {
                "name": "Kontakt-Vorbereitung",
                "description": "Personalisierte Nachrichten erstellen",
                "required_data": ["matching"],
                "ai_driven": True,
                "skipable": True,
                "iterable": True
            },
            "outreach_execution": {
                "name": "Kontakt",
                "description": "Kunden kontaktieren",
                "required_data": ["outreach_preparation"],
                "ai_driven": False,
                "skipable": False,
                "iterable": True
            },
            "follow_up": {
                "name": "Follow-up",
                "description": "Reaktionen verfolgen",
                "required_data": ["outreach_execution"],
                "ai_driven": True,
                "skipable": True,
                "iterable": True
            },
            "optimization": {
                "name": "Optimierung",
                "description": "Prozess verbessert werden",
                "required_data": [],
                "ai_driven": True,
                "skipable": True,
                "iterable": True
            }
        }
        
        # Define default transitions
        self.transitions = [
            # Forward transitions
            FlowTransition("initialization", "discovery", FlowAction.FORWARD),
            FlowTransition("discovery", "search", FlowAction.FORWARD),
            FlowTransition("search", "analysis", FlowAction.FORWARD),
            FlowTransition("analysis", "profiling", FlowAction.FORWARD),
            FlowTransition("profiling", "matching", FlowAction.FORWARD),
            FlowTransition("matching", "outreach_preparation", FlowAction.FORWARD),
            FlowTransition("outreach_preparation", "outreach_execution", FlowAction.FORWARD),
            FlowTransition("outreach_execution", "follow_up", FlowAction.FORWARD),
            
            # Backward transitions (backtracking)
            FlowTransition("search", "discovery", FlowAction.BACKWARD),
            FlowTransition("analysis", "search", FlowAction.BACKWARD),
            FlowTransition("profiling", "analysis", FlowAction.BACKWARD),
            FlowTransition("matching", "profiling", FlowAction.BACKWARD),
            FlowTransition("outreach_preparation", "matching", FlowAction.BACKWARD),
            FlowTransition("outreach_execution", "outreach_preparation", FlowAction.BACKWARD),
            
            # Skip transitions
            FlowTransition("discovery", "search", FlowAction.SKIP),
            FlowTransition("analysis", "profiling", FlowAction.SKIP),
            FlowTransition("profiling", "matching", FlowAction.SKIP),
            FlowTransition("outreach_preparation", "outreach_execution", FlowAction.SKIP),
            
            # Iterate transitions (loops)
            FlowTransition("discovery", "discovery", FlowAction.ITERATE),
            FlowTransition("search", "search", FlowAction.ITERATE),
            FlowTransition("analysis", "analysis", FlowAction.ITERATE),
            FlowTransition("profiling", "profiling", FlowAction.ITERATE),
            FlowTransition("matching", "matching", FlowAction.ITERATE),
            FlowTransition("outreach_preparation", "outreach_preparation", FlowAction.ITERATE),
            FlowTransition("outreach_execution", "outreach_execution", FlowAction.ITERATE),
            
            # Branch transitions (alternative paths)
            FlowTransition("search", "matching", FlowAction.BRANCH),
            FlowTransition("analysis", "matching", FlowAction.BRANCH),
            FlowTransition("optimization", "discovery", FlowAction.BRANCH),
            FlowTransition("optimization", "search", FlowAction.BRANCH),
            
            # Modify transitions (editing previous steps)
            FlowTransition("profiling", "user_profile", FlowAction.MODIFY),
            FlowTransition("matching", "user_profile", FlowAction.MODIFY),
        ]
    
    def initialize_flow(self, goals: List[str] = None) -> FlowState:
        """Initialize a new flow with optional goals."""
        self.flow_goals = goals or []
        self.current_state = FlowState(
            current_step="initialization",
            available_transitions=self._get_available_transitions("initialization"),
            context={"goals": self.flow_goals}
        )
        return self.current_state
    
    def _get_available_transitions(self, current_step: str) -> List[FlowAction]:
        """Get available transitions from current step."""
        available = []
        
        for transition in self.transitions:
            if transition.from_step == current_step:
                # Check if transition condition is met
                if transition.condition is None or transition.condition(self.current_state):
                    available.append(transition)
        
        return available
    
    def transition_to(self, target_step: str, action: FlowAction = FlowAction.FORWARD) -> bool:
        """Transition to a specific step."""
        if not self.current_state:
            logger.error("Flow not initialized")
            return False
        
        # Find matching transition
        matching_transitions = [
            t for t in self.transitions
            if t.from_step == self.current_state.current_step
            and t.to_step == target_step
            and t.action == action
        ]
        
        if not matching_transitions:
            logger.warning(f"No valid transition found from {self.current_state.current_step} to {target_step}")
            return False
        
        # Record history
        self._record_transition(self.current_state.current_step, target_step, action)
        
        # Update state
        self.current_state.mark_completed(self.current_state.current_step)
        self.current_state.current_step = target_step
        self.current_state.available_transitions = self._get_available_transitions(target_step)
        
        logger.info(f"Flow transition: {self.current_state.current_step} -> {target_step} ({action.value})")
        return True
    
    def modify_step(self, step: str, new_data: Dict[str, Any]) -> bool:
        """Modify data for a specific step."""
        if not self.current_state:
            return False
        
        # Update context
        self.current_state.context[step] = {
            **self.current_state.context.get(step, {}),
            **new_data
        }
        
        logger.info(f"Modified step {step} with data: {new_data}")
        return True
    
    def ai_suggest_next_step(self) -> Optional[Dict[str, Any]]:
        """Let AI suggest next steps based on current context."""
        if not self.current_state:
            return None
        
        # Get available transitions
        available = self._get_available_transitions(self.current_state.current_step)
        
        if not available:
            return None
        
        # Score each transition based on context
        scored_transitions = []
        for transition in available:
            score = self._calculate_transition_score(transition)
            scored_transitions.append((transition, score))
        
        # Sort by score
        scored_transitions.sort(key=lambda x: x[1], reverse=True)
        
        # Get top suggestions
        top_suggestions = []
        for transition, score in scored_transitions[:3]:  # Top 3
            suggestion = {
                "action": transition.action.value,
                "target_step": transition.to_step,
                "confidence": score,
                "reasoning": self._get_suggestion_reasoning(transition, score),
                "skipable": self.flow_steps.get(transition.to_step, {}).get("skipable", False),
                "iterable": self.flow_steps.get(transition.to_step, {}).get("iterable", False)
            }
            top_suggestions.append(suggestion)
        
        return {
            "current_step": self.current_state.current_step,
            "suggestions": top_suggestions,
            "context": self.current_state.context
        }
    
    def _calculate_transition_score(self, transition: FlowTransition) -> float:
        """Calculate score for a transition based on context."""
        base_score = 0.5
        
        # Prefer forward progress for initial steps
        transition_order = ["initialization", "discovery", "search", "analysis", 
                          "profiling", "matching", "outreach_preparation", "outreach_execution"]
        try:
            current_idx = transition_order.index(transition.from_step)
            target_idx = transition_order.index(transition.to_step)
            
            if transition.action == FlowAction.FORWARD and target_idx > current_idx:
                base_score += 0.3
            elif transition.action == FlowAction.BACKWARD:
                base_score -= 0.2
            elif transition.action == FlowAction.ITERATE:
                # Iteration is good for complex steps
                if self.flow_steps.get(transition.from_step, {}).get("iterable", False):
                    base_score += 0.2
        except ValueError:
            pass
        
        # Consider user preferences
        if transition.to_step in self.user_preferences.get("preferred_steps", []):
            base_score += 0.2
        
        # Consider flow goals
        if transition.to_step in self.flow_goals:
            base_score += 0.3
        
        # Available data check
        required_data = self.flow_steps.get(transition.to_step, {}).get("required_data", [])
        if all(req in self.current_state.completed_steps for req in required_data):
            base_score += 0.2
        
        return min(max(base_score, 0.0), 1.0)  # Clamp between 0 and 1
    
    def _get_suggestion_reasoning(self, transition: FlowTransition, score: float) -> str:
        """Get reasoning for transition suggestion."""
        reasoning_parts = []
        
        if transition.action == FlowAction.FORWARD:
            reasoning_parts.append("Natürliche Weiterentwicklung")
        elif transition.action == FlowAction.BACKWARD:
            reasoning_parts.append("Zurück zu vorherigem Schritt")
        elif transition.action == FlowAction.ITERATE:
            reasoning_parts.append("Verfeinerung für bessere Ergebnisse")
        elif transition.action == FlowAction.SKIP:
            reasoning_parts.append("Zeitersparnis durch Überspringen")
        
        if score > 0.8:
            reasoning_parts.append("Hohe Relevanz für dein Ziel")
        elif score > 0.5:
            reasoning_parts.append("Gute Option basierend auf Kontext")
        
        return ", ".join(reasoning_parts) if reasoning_parts else "Basierend auf aktuellem Kontext"
    
    def _record_transition(self, from_step: str, to_step: str, action: FlowAction):
        """Record transition in history."""
        self.flow_history.append({
            "from_step": from_step,
            "to_step": to_step,
            "action": action.value,
            "timestamp": self._current_timestamp()
        })
    
    def _current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def get_flow_summary(self) -> Dict[str, Any]:
        """Get summary of current flow state."""
        if not self.current_state:
            return {}
        
        return {
            "current_step": self.current_state.current_step,
            "completed_steps": self.current_state.completed_steps,
            "available_transitions": [t.action.value for t in self.current_state.available_transitions],
            "progress": len(self.current_state.completed_steps) / len(self.flow_steps),
            "context_summary": {k: type(v).__name__ for k, v in self.current_state.context.items()}
        }
    
    def handle_user_intent(self, intent: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Handle user intent and suggest actions."""
        if not self.current_state:
            return None
        
        self.current_state.user_intent = intent
        
        # Update context
        if context:
            self.current_state.context.update(context)
        
        # Analyze intent and suggest actions
        intent_actions = self._analyze_intent(intent)
        
        return {
            "intent": intent,
            "suggested_actions": intent_actions,
            "ai_suggestions": self.ai_suggest_next_step()
        }
    
    def _analyze_intent(self, intent: str) -> List[Dict[str, Any]]:
        """Analyze user intent and suggest appropriate actions."""
        actions = []
        
        # Simple keyword-based intent analysis
        # In production, this would use the LLM
        intent_lower = intent.lower()
        
        if any(word in intent_lower for word in ["zurück", "nochmal", "ändern", "anders"]):
            actions.append({
                "action": "backtrack",
                "target_step": self.current_state.completed_steps[-1] if self.current_state.completed_steps else None,
                "confidence": 0.8
            })
        
        if any(word in intent_lower for word in ["überspringen", "direkt", "später", "jetzt nicht"]):
            actions.append({
                "action": "skip",
                "target_step": self._get_next_skippable_step(),
                "confidence": 0.7
            })
        
        if any(word in intent_lower for word in ["besser", "verbessern", "optimieren", "anders"]):
            actions.append({
                "action": "iterate",
                "target_step": self.current_state.current_step,
                "confidence": 0.9
            })
        
        if any(word in intent_lower for word in ["fertig", "weiter", "nächster Schritt"]):
            actions.append({
                "action": "forward",
                "target_step": self._get_next_step(),
                "confidence": 0.9
            })
        
        return actions
    
    def _get_next_step(self) -> Optional[str]:
        """Get next logical step."""
        if not self.current_state:
            return None
        
        # Find first forward transition
        for transition in self.current_state.available_transitions:
            if transition.action == FlowAction.FORWARD:
                return transition.to_step
        
        return None
    
    def _get_next_skippable_step(self) -> Optional[str]:
        """Get next skippable step."""
        if not self.current_state:
            return None
        
        for step_name, step_info in self.flow_steps.items():
            if step_info.get("skipable", False) and step_name not in self.current_state.completed_steps:
                return step_name
        
        return self._get_next_step()


# Global flow engine instance
_flow_engine: Optional[DynamicFlowEngine] = None


def get_flow_engine() -> DynamicFlowEngine:
    """Get global flow engine instance."""
    global _flow_engine
    if _flow_engine is None:
        _flow_engine = DynamicFlowEngine()
    return _flow_engine