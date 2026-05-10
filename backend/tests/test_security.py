"""Unit tests for security utilities."""

import pytest
from app.security import (
    RateLimiter,
    SecurityMiddleware,
    InputValidator,
    validate_request_body
)


class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_initial_rate_limit(self):
        """Test initial requests are allowed."""
        limiter = RateLimiter(requests_per_minute=10)
        
        for i in range(10):
            is_allowed, _ = limiter.is_allowed("test_key")
            assert is_allowed == True
    
    def test_rate_limit_exceeded(self):
        """Test that rate limit is enforced."""
        limiter = RateLimiter(requests_per_minute=5)
        
        # First 5 requests should be allowed
        for i in range(5):
            is_allowed, _ = limiter.is_allowed("test_key")
            assert is_allowed == True
        
        # Next request should be blocked
        is_allowed, message = limiter.is_allowed("test_key")
        assert is_allowed == False
        assert "Rate limit exceeded" in message
    
    def test_different_keys_separate_limits(self):
        """Test that different keys have separate rate limits."""
        limiter = RateLimiter(requests_per_minute=3)
        
        # Different keys should have separate limits
        for i in range(3):
            assert limiter.is_allowed("key1")[0] == True
        
        # key2 should still be allowed
        assert limiter.is_allowed("key2")[0] == True
        
        # key1 should be blocked
        assert limiter.is_allowed("key1")[0] == False


class TestInputValidator:
    """Tests for InputValidator class."""
    
    def test_validate_text_input_empty(self):
        """Test validation of empty input."""
        is_valid, error = InputValidator.validate_text_input("")
        assert is_valid == True
        assert error is None
    
    def test_validate_text_input_valid(self):
        """Test validation of valid input."""
        is_valid, error = InputValidator.validate_text_input("Hello, this is a valid message!")
        assert is_valid == True
        assert error is None
    
    def test_validate_text_input_too_long(self):
        """Test validation rejects too long input."""
        long_text = "a" * 11000
        is_valid, error = InputValidator.validate_text_input(long_text, max_length=10000)
        assert is_valid == False
        assert "too long" in error.lower()
    
    def test_validate_sql_injection(self):
        """Test SQL injection detection."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1 UNION SELECT * FROM users",
            "' OR 1=1--"
        ]
        
        for malicious_input in malicious_inputs:
            is_valid, error = InputValidator.validate_text_input(malicious_input)
            assert is_valid == False
            assert "Invalid input detected" in error
    
    def test_validate_xss(self):
        """Test XSS detection."""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='malicious.html'>"
        ]
        
        for malicious_input in malicious_inputs:
            is_valid, error = InputValidator.validate_text_input(malicious_input)
            assert is_valid == False
            assert "Invalid input detected" in error
    
    def test_sanitize_url_valid(self):
        """Test URL sanitization for valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://example.com/path",
            "https://subdomain.example.com:8080/page"
        ]
        
        for url in valid_urls:
            is_valid, error, sanitized = InputValidator.sanitize_url(url)
            assert is_valid == True
            assert error is None
            assert sanitized == url
    
    def test_sanitize_url_invalid(self):
        """Test URL sanitization rejects invalid URLs."""
        malicious_urls = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "file:///etc/passwd",
            "http://localhost:8000"  # Would be rejected in production
        ]
        
        for url in malicious_urls:
            is_valid, error, sanitized = InputValidator.sanitize_url(url)
            # localhost should be rejected, javascript/data should also be rejected
            if "localhost" in url:
                assert is_valid == False
                assert "not allowed" in error.lower()
            elif "javascript:" in url or "data:" in url:
                assert is_valid == False
    
    def test_validate_message_content_valid(self):
        """Test message content validation for valid content."""
        valid_messages = [
            "Hello, how are you?",
            "This is a test message with some content.",
            "Can you help me with something?"
        ]
        
        for message in valid_messages:
            is_valid, error = InputValidator.validate_message_content(message)
            assert is_valid == True
            assert error is None
    
    def test_validate_message_content_repetitive(self):
        """Test message content validation rejects repetitive content."""
        repetitive = "a" * 1000
        is_valid, error = InputValidator.validate_message_content(repetitive)
        assert is_valid == False
        assert "repetitive" in error.lower()
    
    def test_validate_request_body_valid(self):
        """Test request body validation."""
        body = {"field1": "value1", "field2": "value2"}
        is_valid, error = validate_request_body(body)
        assert is_valid == True
        assert error is None
    
    def test_validate_request_body_missing_required(self):
        """Test request body validation with missing required fields."""
        body = {"field1": "value1"}
        is_valid, error = validate_request_body(body, required_fields=["field1", "field2"])
        assert is_valid == False
        assert "missing" in error.lower()
    
    def test_validate_request_body_too_long(self):
        """Test request body validation with too long field."""
        body = {"field1": "a" * 2000}
        is_valid, error = validate_request_body(body, max_field_length=1000)
        assert is_valid == False
        assert "maximum length" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])