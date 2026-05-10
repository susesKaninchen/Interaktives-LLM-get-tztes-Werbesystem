"""Conversation state manager with persistence and validation."""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Immutable conversation state with persistence."""
    
    # Core conversation data
    conversation_id: int
    current_phase: str = "search"
    intent: str = ""
    
    # Search and selection data
    search_results: list[dict] = field(default_factory=list)
    selected_company: Optional[dict] = None
    company_profile: Optional[dict] = None
    
    # User and matching data
    user_profile: Optional[dict] = None
    matching_results: list[dict] = field(default_factory=list)
    
    # Generated content
    generated_content: str = ""
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convert state to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert state to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConversationState":
        """Create state from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "ConversationState":
        """Create state from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def update(self, **kwargs) -> "ConversationState":
        """Create a new state with updated fields."""
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        current_dict["updated_at"] = datetime.now().isoformat()
        return ConversationState.from_dict(current_dict)
    
    def with_phase(self, phase: str) -> "ConversationState":
        """Create new state with updated phase."""
        return self.update(current_phase=phase)
    
    def with_search_results(self, results: list[dict]) -> "ConversationState":
        """Create new state with search results."""
        return self.update(search_results=results)
    
    def with_selected_company(self, company: dict) -> "ConversationState":
        """Create new state with selected company."""
        return self.update(selected_company=company)
    
    def with_company_profile(self, profile: dict) -> "ConversationState":
        """Create new state with company profile."""
        return self.update(company_profile=profile)
    
    def with_user_profile(self, profile: dict) -> "ConversationState":
        """Create new state with user profile."""
        return self.update(user_profile=profile)
    
    def with_matching_results(self, results: list[dict]) -> "ConversationState":
        """Create new state with matching results."""
        return self.update(matching_results=results)
    
    def with_generated_content(self, content: str) -> "ConversationState":
        """Create new state with generated content."""
        return self.update(generated_content=content)
    
    def with_intent(self, intent: str) -> "ConversationState":
        """Create new state with intent."""
        return self.update(intent=intent)
    
    def validate(self) -> bool:
        """Validate state consistency."""
        try:
            # Validate conversation_id
            if not isinstance(self.conversation_id, int) or self.conversation_id <= 0:
                logger.error(f"Invalid conversation_id: {self.conversation_id}")
                return False
            
            # Validate phase
            valid_phases = {"search", "select", "profile", "matching", "outreach"}
            if self.current_phase not in valid_phases:
                logger.warning(f"Unknown phase: {self.current_phase}")
            
            # Validate intent
            valid_intents = {"search", "crawl_url", "matching", "outreach", 
                           "user_profile", "template", "knowledge", "general_chat"}
            if self.intent and self.intent not in valid_intents:
                logger.warning(f"Unknown intent: {self.intent}")
            
            # Validate data consistency
            if self.selected_company and not self.search_results:
                logger.warning("Selected company without search results")
            
            if self.company_profile and not self.selected_company:
                logger.warning("Company profile without selected company")
            
            return True
        except Exception as e:
            logger.error(f"State validation failed: {e}")
            return False
    
    def has_company_data(self) -> bool:
        """Check if state has company data."""
        return bool(self.selected_company or self.company_profile)
    
    def can_proceed_to_matching(self) -> bool:
        """Check if state can proceed to matching phase."""
        return self.has_company_data() and bool(self.user_profile)
    
    def can_proceed_to_outreach(self) -> bool:
        """Check if state can proceed to outreach phase."""
        return self.can_proceed_to_matching() and bool(self.matching_results)


class ConversationStateManager:
    """Manages conversation state with persistence."""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.state_dir = self.data_dir / "conversation_states"
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_state_file(self, conversation_id: int) -> Path:
        """Get state file path for conversation."""
        return self.state_dir / f"{conversation_id}.json"
    
    async def load_state(self, conversation_id: int) -> ConversationState:
        """Load state from disk or create new one."""
        state_file = self._get_state_file(conversation_id)
        
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = ConversationState.from_json(f.read())
                    if state.validate():
                        logger.info(f"Loaded state for conversation {conversation_id}")
                        return state
                    else:
                        logger.warning(f"Invalid state for conversation {conversation_id}, creating new")
            except Exception as e:
                logger.error(f"Failed to load state for conversation {conversation_id}: {e}")
        
        # Create new state
        return ConversationState(conversation_id=conversation_id)
    
    async def save_state(self, state: ConversationState) -> bool:
        """Save state to disk."""
        if not state.validate():
            logger.error(f"Cannot save invalid state for conversation {state.conversation_id}")
            return False
        
        try:
            state_file = self._get_state_file(state.conversation_id)
            with open(state_file, "w", encoding="utf-8") as f:
                f.write(state.to_json())
            logger.info(f"Saved state for conversation {state.conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save state for conversation {state.conversation_id}: {e}")
            return False
    
    async def delete_state(self, conversation_id: int) -> bool:
        """Delete state file."""
        try:
            state_file = self._get_state_file(conversation_id)
            if state_file.exists():
                state_file.unlink()
                logger.info(f"Deleted state for conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete state for conversation {conversation_id}: {e}")
            return False
    
    async def list_conversations(self) -> list[int]:
        """List all conversation IDs with saved state."""
        try:
            conversations = []
            for state_file in self.state_dir.glob("*.json"):
                try:
                    conversation_id = int(state_file.stem)
                    conversations.append(conversation_id)
                except ValueError:
                    continue
            return sorted(conversations)
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []


# Global instance
_state_manager: Optional[ConversationStateManager] = None


def get_state_manager() -> ConversationStateManager:
    """Get global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = ConversationStateManager()
    return _state_manager