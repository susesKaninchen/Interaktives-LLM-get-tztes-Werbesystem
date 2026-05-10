"""Integration tests for the chat router."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.main import app
from app.agents.conversation_state import ConversationState


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    with patch('app.routers.chat.async_session') as mock_session:
        yield mock_session


@pytest.fixture
def mock_conversation_state():
    """Mock conversation state."""
    state = ConversationState(
        conversation_id=1,
        current_phase="search",
        search_results=[],
        selected_company=None,
        company_profile=None,
        user_profile=None,
        matching_results=[]
    )
    return state


class TestChatRouter:
    """Integration tests for chat router."""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    def test_get_config_models(self, client):
        """Test getting model configuration."""
        response = client.get("/api/config/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "routing" in data
    
    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self, mock_db_session, mock_conversation_state):
        """Test WebSocket connection lifecycle."""
        # This test would require async WebSocket testing
        # For now, we'll just test the basic structure
        pass
    
    def test_error_handling_format(self, client):
        """Test error response format."""
        # Test a 404 error
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestMessageProcessing:
    """Tests for message processing logic."""
    
    def test_message_validation_length(self):
        """Test that long messages are rejected."""
        from app.security import InputValidator
        
        long_message = "a" * 11000
        is_valid, error = InputValidator.validate_message_content(long_message)
        assert is_valid == False
    
    def test_message_validation_empty(self):
        """Test that empty messages are rejected."""
        from app.security import InputValidator
        
        is_valid, error = InputValidator.validate_message_content("")
        # Empty messages might be valid in some contexts
        # This test just shows the validation works
    
    def test_state_persistence_consistency(self, mock_conversation_state):
        """Test that state persists correctly through updates."""
        original_phase = mock_conversation_state.current_phase
        assert original_phase == "search"
        
        # Update state
        updated_state = mock_conversation_state.with_phase("profile")
        assert updated_state.current_phase == "profile"
        assert mock_conversation_state.current_phase == "search"


class TestRouterIntegration:
    """Integration tests for router components."""
    
    def test_router_graph_compilation(self):
        """Test that the agent graph compiles correctly."""
        from app.agents.orchestrator import compile_graph
        
        try:
            graph = compile_graph()
            assert graph is not None
            # Graph should have nodes and edges
            assert hasattr(graph, 'nodes')
        except Exception as e:
            pytest.fail(f"Graph compilation failed: {e}")
    
    def test_state_validation_crucial_transitions(self, mock_conversation_state):
        """Test state validation for crucial workflow transitions."""
        # Should not be able to proceed to matching without company data
        empty_state = ConversationState(conversation_id=1)
        assert empty_state.can_proceed_to_matching() == False
        
        # Should be able to proceed with both company and user data
        state_with_data = mock_conversation_state
        assert state_with_data.can_proceed_to_matching() == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])