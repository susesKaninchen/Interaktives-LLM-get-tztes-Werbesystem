"""Performance optimization utilities for the application."""

import time
import hashlib
import json
import logging
from functools import wraps
from typing import Optional, Callable, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ResponseCache:
    """Simple in-memory response cache with TTL."""
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """Initialize cache.
        
        Args:
            ttl: Time to live in seconds
            max_size: Maximum number of cached items
        """
        self.ttl = ttl
        self.max_size = max_size
        self.cache: dict[str, tuple[any, float]] = {}
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_parts = []
        
        # Add positional args
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif arg is None:
                key_parts.append("None")
            else:
                # For complex objects, use hash
                try:
                    key_parts.append(str(hash(str(arg))))
                except:
                    key_parts.append(str(id(arg)))
        
        # Add keyword args
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
            elif v is None:
                key_parts.append(f"{k}:None")
            else:
                try:
                    key_parts.append(f"{k}:{hash(str(v))}")
                except:
                    key_parts.append(f"{k}:{id(v)}")
        
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()
    
    def get(self, *args, **kwargs) -> Optional[Any]:
        """Get cached value if exists and not expired."""
        key = self._generate_key(*args, **kwargs)
        
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        
        # Check if expired
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, *args, value: Any = None, **kwargs) -> None:
        """Set value in cache."""
        key = self._generate_key(*args, **kwargs)
        
        # Remove old entries if cache is full
        if len(self.cache) >= self.max_size:
            # Simple FIFO: remove oldest entries (bottom 10%)
            keys_to_remove = list(self.cache.keys())[:int(self.max_size * 0.1)]
            for k in keys_to_remove:
                del self.cache[k]
        
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def cleanup(self) -> int:
        """Remove expired entries and return count removed."""
        now = time.time()
        keys_to_remove = []
        
        for key, (_, timestamp) in self.cache.items():
            if now - timestamp > self.ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        return len(keys_to_remove)


# Global cache instances
llm_cache = ResponseCache(ttl=1800, max_size=500)  # 30 minutes, 500 items
search_cache = ResponseCache(ttl=900, max_size=1000)  # 15 minutes, 1000 items


def cache_response(cache: ResponseCache = llm_cache):
    """Decorator to cache function responses."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Try to get from cache
            cached_value = cache.get(*args, **kwargs)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache.set(*args, value=result, **kwargs)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Try to get from cache
            cached_value = cache.get(*args, **kwargs)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(*args, value=result, **kwargs)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceMonitor:
    """Monitor and log function performance."""
    
    def __init__(self, slow_threshold: float = 1.0):
        """Initialize performance monitor.
        
        Args:
            slow_threshold: Threshold in seconds to consider a function "slow"
        """
        self.slow_threshold = slow_threshold
        self.call_stats: dict[str, dict] = {}
    
    def monitor(self, func: Callable) -> Callable:
        """Decorator to monitor function performance."""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                self._record_call(func.__name__, elapsed)
                
                if elapsed > self.slow_threshold:
                    logger.warning(f"Slow function call: {func.__name__} took {elapsed:.2f}s")
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                self._record_call(func.__name__, elapsed, error=True)
                logger.error(f"Function {func.__name__} failed after {elapsed:.2f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                self._record_call(func.__name__, elapsed)
                
                if elapsed > self.slow_threshold:
                    logger.warning(f"Slow function call: {func.__name__} took {elapsed:.2f}s")
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                self._record_call(func.__name__, elapsed, error=True)
                logger.error(f"Function {func.__name__} failed after {elapsed:.2f}s: {e}")
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    def _record_call(self, func_name: str, elapsed: float, error: bool = False):
        """Record function call statistics."""
        if func_name not in self.call_stats:
            self.call_stats[func_name] = {
                "count": 0,
                "total_time": 0.0,
                "errors": 0,
                "max_time": 0.0,
                "min_time": float('inf')
            }
        
        stats = self.call_stats[func_name]
        stats["count"] += 1
        stats["total_time"] += elapsed
        stats["max_time"] = max(stats["max_time"], elapsed)
        stats["min_time"] = min(stats["min_time"], elapsed)
        
        if error:
            stats["errors"] += 1
    
    def get_stats(self, func_name: Optional[str] = None) -> dict:
        """Get performance statistics.
        
        Args:
            func_name: Specific function name, or None for all functions
            
        Returns:
            Dictionary with performance statistics
        """
        if func_name:
            return self.call_stats.get(func_name, {})
        
        return self.call_stats
    
    def reset_stats(self):
        """Reset all statistics."""
        self.call_stats.clear()


# Global performance monitor
performance_monitor = PerformanceMonitor(slow_threshold=2.0)


def monitor_performance(func: Callable) -> Callable:
    """Convenient decorator to monitor function performance."""
    return performance_monitor.monitor(func)


async def cleanup_caches():
    """Periodic cache cleanup."""
    llm_cleanup = llm_cache.cleanup()
    search_cleanup = search_cache.cleanup()
    
    total = llm_cleanup + search_cleanup
    if total > 0:
        logger.info(f"Cache cleanup: removed {total} expired entries")


def get_cache_stats() -> dict:
    """Get statistics about cache usage."""
    return {
        "llm_cache": {
            "size": len(llm_cache.cache),
            "max_size": llm_cache.max_size,
            "ttl": llm_cache.ttl
        },
        "search_cache": {
            "size": len(search_cache.cache),
            "max_size": search_cache.max_size,
            "ttl": search_cache.ttl
        }
    }


def get_performance_stats() -> dict:
    """Get performance statistics."""
    return performance_monitor.get_stats()