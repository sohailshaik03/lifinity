# utils/cache_manager.py
"""
Centralized caching utilities with Redis support for production performance
"""
from __future__ import annotations

import streamlit as st
from functools import wraps
from typing import Any, Callable, Optional
import hashlib
import json
import pickle
import os
from datetime import timedelta

# Try to import Redis
try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None


class CacheManager:
    """Manage application-wide caching with Redis fallback to Streamlit cache"""
    
    # Cache TTLs in seconds
    TTL_SHORT = 60           # 1 minute - frequently changing data
    TTL_MEDIUM = 300         # 5 minutes - semi-static data
    TTL_LONG = 3600          # 1 hour - static reference data
    TTL_VERY_LONG = 86400    # 24 hours - rarely changing data
    
    def __init__(self):
        """Initialize cache manager with Redis if available"""
        self.redis_client: Optional[Redis] = None
        self.use_redis = False
        
        if REDIS_AVAILABLE:
            redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_HOST")
            if redis_url:
                try:
                    # Try to connect to Redis
                    if redis_url.startswith("redis://") or redis_url.startswith("rediss://"):
                        self.redis_client = redis.from_url(
                            redis_url,
                            decode_responses=False,  # We'll handle encoding
                            socket_connect_timeout=5,
                            socket_timeout=5
                        )
                    else:
                        # Assume it's a host:port format
                        host = redis_url.split(":")[0] if ":" in redis_url else redis_url
                        port = int(redis_url.split(":")[1]) if ":" in redis_url else 6379
                        password = os.getenv("REDIS_PASSWORD")
                        
                        self.redis_client = Redis(
                            host=host,
                            port=port,
                            password=password,
                            decode_responses=False,
                            socket_connect_timeout=5,
                            socket_timeout=5,
                            db=0
                        )
                    
                    # Test connection
                    self.redis_client.ping()
                    self.use_redis = True
                    print("✅ Redis cache connected successfully")
                except Exception as e:
                    print(f"⚠️ Redis connection failed: {e}. Falling back to Streamlit cache.")
                    self.redis_client = None
                    self.use_redis = False
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        if self.use_redis and self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return pickle.loads(data)
            except Exception as e:
                print(f"Redis get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = TTL_MEDIUM):
        """Set value in cache with TTL"""
        if self.use_redis and self.redis_client:
            try:
                serialized = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
                return True
            except Exception as e:
                print(f"Redis set error: {e}")
        return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                print(f"Redis delete error: {e}")
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern (e.g., 'user:*')"""
        if self.use_redis and self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                print(f"Redis clear pattern error: {e}")
    
    def cache_data(self, ttl: int = TTL_MEDIUM, show_spinner: bool = False):
        """Decorator for caching data with Redis or Streamlit fallback"""
        if self.use_redis:
            # Use Redis-based caching
            def decorator(func: Callable) -> Callable:
                @wraps(func)
                def wrapper(*args, **kwargs):
                    # Generate cache key
                    cache_key = f"{func.__module__}:{func.__name__}:{self.get_cache_key(*args, **kwargs)}"
                    
                    # Try to get from cache
                    cached_value = self.get(cache_key)
                    if cached_value is not None:
                        return cached_value
                    
                    # Execute function and cache result
                    result = func(*args, **kwargs)
                    self.set(cache_key, result, ttl)
                    return result
                return wrapper
            return decorator
        else:
            # Fallback to Streamlit cache
            return st.cache_data(ttl=ttl, show_spinner=show_spinner)
    
    def cache_resource(self, show_spinner: bool = False):
        """Decorator for caching resources (connections, models, etc.)"""
        # Resources are better cached in-memory with Streamlit
        return st.cache_resource(show_spinner=show_spinner)
    
    def clear_all_caches(self):
        """Clear all caches"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.flushdb()
                print("✅ Redis cache cleared")
            except Exception as e:
                print(f"Redis flush error: {e}")
        
        # Also clear Streamlit caches
        st.cache_data.clear()
        st.cache_resource.clear()
    
    @staticmethod
    def get_cache_key(*args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        key_data = {
            'args': [str(arg) for arg in args],  # Convert to strings for JSON
            'kwargs': {k: str(v) for k, v in kwargs.items()}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter (useful for rate limiting, analytics)"""
        if self.use_redis and self.redis_client:
            try:
                return self.redis_client.incr(key, amount)
            except Exception as e:
                print(f"Redis incr error: {e}")
        return 0
    
    def set_with_expiry(self, key: str, value: Any, seconds: int):
        """Set a key with automatic expiry"""
        return self.set(key, value, ttl=seconds)
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        stats = {
            "backend": "redis" if self.use_redis else "streamlit",
            "redis_available": REDIS_AVAILABLE,
            "redis_connected": self.use_redis
        }
        
        if self.use_redis and self.redis_client:
            try:
                info = self.redis_client.info()
                stats.update({
                    "total_keys": self.redis_client.dbsize(),
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "hit_rate": info.get("keyspace_hits", 0) / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) * 100
                })
            except Exception as e:
                stats["error"] = str(e)
        
        return stats


# Singleton instance
cache = CacheManager()
