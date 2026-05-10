"""Unit tests for the conversation state manager."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import json

from app.agents.conversation_state import (
    ConversationState, 
    ConversationStateManager,
    get_state_manager
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def state_manager(temp_data_dir):
    """Create a state manager with temporary directory."""
    return ConversationStateManager(temp_data_dir)


@pytest.fixture
def sample_state():
    """Create a sample conversation state."""
    return ConversationState(
        conversation_id=1,
        current_phase="search",
        intent="search",
        search_results=[{"title": "Test", "url": "http://example.com"}],
        selected_company={"name": "Test Company"},
        company_profile={"description": "Test Description"},
        user_profile={"services": ["Web Design"]},
        matching_results=[{"score": 0.9}],
        generated_content="Test content"
    )


class TestConversationState:
    """Tests for ConversationState class."""
    
    def test_create_empty_state(self):
        """Test creating an empty state."""
        state = ConversationState(conversation_id=1)
        assert state.conversation_id == 1
        assert state.current_phase == "search"
        assert state.intent == ""
        assert len(state.search_results) == 0
    
    def test_state_to_dict(self, sample_state):
        """Test converting state to dictionary."""
        state_dict = sample_state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict["conversation_id"] == 1
        assert len(state_state["search_results"]) == 1
    
    def test_state_to_json(self, sample_state):
        """Test converting state to JSON."""
        json_str = sample_state.to_json()
        assert isinstance(json_str, str)
        
        # Parse and verify
        parsed = json.loads(json_str)
        assert parsed["conversation_id"] == 1
    
    def test_state_from_dict(self, sample_state):
        """Test creating state from dictionary."""
        state_dict = sample_state.to_dict()
        new_state = ConversationState.from_dict(state_dict)
        
        assert new_state.conversation_id == sample_state.conversation_id
        assert new_state.current_phase == sample_state.current_phase
    
    def test_state_from_json(self, sample_state):
        """Test creating state from JSON."""
        json_str = sample_state.to_json()
        new_state = ConversationState.from_json(json_str)
        
        assert new_state.conversation_id == sample_state.conversation_id
        assert new_state.current_phase == sample_state.current_phase
    
    def test_update_state(self, sample_state):
        """Test updating state with new values."""
        updated = sample_state.update(current_phase="profile", intent="crawl_url")
        
        assert updated.conversation_id == sample_state.conversation_id
        assert updated.current_phase == "profile"
        assert updated.intent == "crawl_url"
        assert sample_state.current_phase == "search"  # Original unchanged
    
    def test_state_validation_valid(self, sample_state):
        """Test validation of valid state."""
        assert sample_state.validate() == True
    
    def test_state_validation_invalid_id(self):
        """Test validation with invalid conversation ID."""
        state = ConversationState(conversation_id=-1)
        assert state.validate() == False
    
    def test_state_validation_invalid_phase(self):
        """Test validation with invalid phase."""
        state = ConversationState(conversation_id=1, current_phase="invalid")
        # Validation should still pass but log warning
        result = state.validate()
        assert result == True  # No hard validation failure
    
    def test_has_company_data(self, sample_state):
        """Test checking if state has company data."""
        assert sample_state.has_company_data() == True
        
        state = ConversationState(conversation_id=1)
        assert state.has_company_data() == False
    
    def test_can_proceed_to_matching(self, sample_state):
        """Test checking if can proceed to matching."""
        assert sample_state.can_proceed_to_matching() == True
        
        state = ConversationState(conversation_id=1)
        assert state.can_proceed_to_matching() == False
    
    def test_can_proceed_to_outreach(self, sample_state):
        """Test checking if can proceed to outreach."""
        assert sample_state.can_proceed_to_outreach() == True
        
        state = ConversationState(conversation_id=1, user_profile={"services": []})
        assert state.can_proceed_to_outreach() == False


class TestConversationStateManager:
    """Tests for ConversationStateManager class."""
    
    @pytest.mark.asyncio
    async def test_load_new_state(self, state_manager):
        """Test loading a new state."""
        state = await state_manager.load_state(1)
        
        assert isinstance(state, ConversationState)
        assert state.conversation_id == 1
        assert state.current_phase == "search"
    
    @pytest.mark.asyncio
    async def test_save_and_load_state(self, state_manager, sample_state):
        """Test saving and loading state."""
        # Save state
        result = await state_manager.save_state(sample_state)
        assert result == True
        
        # Load state
        loaded_state = await state_manager.load_state(1)
        
        assert loaded_state.conversation_id == sample_state.conversation_id
        assert loaded_state.current_phase == sample_state.current_phase
        assert len(loaded_state.search_results) == len(sample_state.search_results)
    
    @pytest.mark.asyncio
    async def test_save_invalid_state(self, state_manager):
        """Test saving invalid state."""
        invalid_state = ConversationState(conversation_id=-1)
        result = await state_manager.save_state(invalid_state)
        assert result == False
    
    @pytest.mark.asyncio
    async def test_delete_state(self, state_manager, sample_state):
        """Test deleting state."""
        # Save state
        await state_manager.save_state(sample_state)
        
        # Delete state
        result = await state_manager.delete_state(1)
        assert result == True
        
        # Verify deletion
        loaded_state = await state_manager.load_state(1)
        assert loaded_state.conversation_id == 1  # New state created
        assert len(loaded_state.search_results) == 0  # Empty
    
    @pytest.mark.asyncio
    async def test_list_conversations(self, state_manager):
        """Test listing conversations."""
        # Create multiple states
        await state_manager.save_state(ConversationState(conversation_id=1))
        await state_manager.save_state(ConversationState(conversation_id=2))
        await state_manager.save_state(ConversationState(conversation_id=3))
        
        # List conversations
        conversations = await state_manager.list_conversations()
        
        assert len(conversations) == 3
        assert 1 in conversations
        assert 2 in conversations
        assert 3 in conversations


class TestGlobalStateManager:
    """Tests for global state manager instance."""
    
    def test_get_state_manager_singleton(self):
        """Test that global state manager is a singleton."""
        manager1 = get_state_manager()
        manager2 = get_state_manager()
        
        assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])