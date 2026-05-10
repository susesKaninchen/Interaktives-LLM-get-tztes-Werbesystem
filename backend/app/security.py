"""Security middleware for rate limiting, input validation, and request sanitization."""

import time
import ipaddress
import re
from collections import defaultdict
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests: Dict[str, list[float]] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> tuple[bool, Optional[str]]:
        """Check if request is allowed based on rate limits."""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        # Clean old requests
        self.requests[identifier] = [
            timestamp for timestamp in self.requests[identifier]
            if timestamp > hour_ago
        ]
        
        requests = self.requests[identifier]
        
        # Check minute limit
        recent_minute = [t for t in requests if t > minute_ago]
        if len(recent_minute) >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        # Check hour limit
        if len(requests) >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        # Add current request
        self.requests[identifier].append(now)
        return True, None
    
    def cleanup(self):
        """Clean up old entries to prevent memory leaks."""
        now = time.time()
        hour_ago = now - 3600
        
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                timestamp for timestamp in self.requests[identifier]
                if timestamp > hour_ago
            ]
            if not self.requests[identifier]:
                del self.requests[identifier]


# Global rate limiter instance
rate_limiter = RateLimiter()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for rate limiting and input validation."""
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_ip = self._get_client_ip(request)
        
        # Rate limiting
        is_allowed, error_message = rate_limiter.is_allowed(client_ip)
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}: {error_message}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": error_message}
            )
        
        # Security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For can contain multiple IPs, get the first one
            ips = forwarded.split(",")
            return ips[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"


class InputValidator:
    """Input validation and sanitization utilities."""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|alter|create|exec|execute)\b)",
        r"(\b(or|and)\s+\d+\s*=\s*\d+)",
        r"(\b(or|and)\s+['\"].*['\"]\s*=\s*['\"].*['\"])",
        r"(;.*\b(exec|execute|xp_cmdshell)\b)",
        r"(''.*''|.*'')",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]
    
    @staticmethod
    def validate_text_input(text: str, max_length: int = 10000) -> tuple[bool, Optional[str]]:
        """Validate text input for common attacks."""
        if not text:
            return True, None
        
        # Check length
        if len(text) > max_length:
            return False, f"Input too long (max {max_length} characters)"
        
        # Check for SQL injection
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return False, "Invalid input detected"
        
        # Check for XSS
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"XSS pattern detected: {pattern}")
                return False, "Invalid input detected"
        
        return True, None
    
    @staticmethod
    def sanitize_url(url: str) -> tuple[bool, Optional[str], str]:
        """Validate and sanitize URL."""
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            
            # Check protocol
            if parsed.scheme not in ("http", "https"):
                return False, "Only HTTP and HTTPS URLs are allowed", ""
            
            # Check for forbidden patterns
            forbidden_patterns = ["javascript:", "data:", "vbscript:"]
            for pattern in forbidden_patterns:
                if pattern in url.lower():
                    return False, f"Forbidden URL pattern: {pattern}", ""
            
            # Basic URL validation
            if not parsed.netloc:
                return False, "Invalid URL format", ""
            
            # Reject localhost/private IPs in production
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_loopback or ip.is_private or ip.is_link_local:
                    return False, "Private IP addresses not allowed", ""
            except ValueError:
                # Not an IP address, might be a hostname
                pass
            
            return True, None, url
            
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False, "Invalid URL", ""
    
    @staticmethod
    def validate_message_content(content: str) -> tuple[bool, Optional[str]]:
        """Validate chat message content."""
        is_valid, error = InputValidator.validate_text_input(content, max_length=10000)
        if not is_valid:
            return False, error
        
        # Check for extremely repetitive content
        if len(content) > 100:
            # Check if more than 80% of characters are the same
            char_counts = defaultdict(int)
            for char in content:
                char_counts[char] += 1
            
            max_count = max(char_counts.values())
            if max_count / len(content) > 0.8:
                return False, "Message contains too much repetitive content"
        
        return True, None


def validate_request_body(request_body: dict, required_fields: list = None, 
                         max_field_length: int = 1000) -> tuple[bool, Optional[str]]:
    """Validate request body."""
    if not isinstance(request_body, dict):
        return False, "Invalid request body format"
    
    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in request_body:
                return False, f"Missing required field: {field}"
    
    # Validate field lengths
    for key, value in request_body.items():
        if isinstance(value, str) and len(value) > max_field_length:
            return False, f"Field '{key}' exceeds maximum length of {max_field_length}"
    
    return True, None


# Cleanup function for rate limiter (call periodically)
async def cleanup_rate_limiter():
    """Clean up old rate limiter entries."""
    rate_limiter.cleanup()
    logger.info("Rate limiter cleanup completed")