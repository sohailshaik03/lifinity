"""Centralized caching utilities with Redis/Upstash support for production performance.

Provides three-tier caching: Upstash REST API → Redis → Streamlit cache
Supports distributed caching for serverless deployments.
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
from loguru import logger

# Try to import Redis
try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

# Try to import requests for Upstash REST API
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class CacheManager:
    """Manage application-wide caching with Redis/Upstash fallback to Streamlit cache.
    
    Implements three-tier caching strategy:
    1. Upstash REST API (best for serverless/Streamlit Cloud)
    2. Standard Redis (for self-hosted deployments)
    3. Streamlit cache (fallback when no external cache available)
    
    Attributes:
        TTL_SHORT: 60 seconds for frequently changing data
        TTL_MEDIUM: 300 seconds for semi-static data
        TTL_LONG: 3600 seconds for static reference data
        TTL_VERY_LONG: 86400 seconds for rarely changing data
    """
    
    # Cache TTLs in seconds
    TTL_SHORT = 60           # 1 minute - frequently changing data
    TTL_MEDIUM = 300         # 5 minutes - semi-static data
    TTL_LONG = 3600          # 1 hour - static reference data
    TTL_VERY_LONG = 86400    # 24 hours - rarely changing data
    
    def __init__(self):
        """Initialize cache manager with Redis/Upstash if available"""
        self.redis_client: Optional[Redis] = None
        self.upstash_rest_url: Optional[str] = None
        self.upstash_rest_token: Optional[str] = None
        self.use_redis = False
        self.use_upstash_rest = False
        
        # Try Upstash REST API first (better for serverless)
        upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
        upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        
        if upstash_url and upstash_token and REQUESTS_AVAILABLE:
            try:
                # Test Upstash REST API
                headers = {"Authorization": f"Bearer {upstash_token}"}
                response = requests.get(f"{upstash_url}/ping", headers=headers, timeout=5)
                if response.status_code == 200:
                    self.upstash_rest_url = upstash_url
                    self.upstash_rest_token = upstash_token
                    self.use_upstash_rest = True
                    logger.info("Upstash Redis REST API connected successfully")
                    return
            except Exception as e:
                logger.warning(f"Upstash REST API connection failed: {e}")
        
        # Fallback to standard Redis connection
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
                    logger.info("Redis cache connected successfully")
                except Exception as e:
                    logger.warning(f"Redis connection failed: {e}. Falling back to Streamlit cache.")
                    self.redis_client = None
                    self.use_redis = False
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        # Try Upstash REST API first
        if self.use_upstash_rest:
            try:
                headers = {"Authorization": f"Bearer {self.upstash_rest_token}"}
                response = requests.get(
                    f"{self.upstash_rest_url}/get/{key}",
                    headers=headers,
                    timeout=3
                )
                if response.status_code == 200:
                    result = response.json().get("result")
                    if result:
                        # Upstash stores the value as-is, we need to decode from base64
                        import base64
                        # The result is already our base64 encoded pickled data
                        decoded = base64.b64decode(result)
                        return pickle.loads(decoded)
            except Exception as e:
                logger.debug(f"Upstash REST get error: {e}")
        
        # Fallback to standard Redis
        if self.use_redis and self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return pickle.loads(data)
            except Exception as e:
                logger.debug(f"Redis get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = TTL_MEDIUM):
        """Set value in cache with TTL"""
        # Try Upstash REST API first
        if self.use_upstash_rest:
            try:
                import base64
                # Serialize with pickle and encode to base64
                serialized = pickle.dumps(value)
                # Upstash REST API needs the data in the request body
                headers = {
                    "Authorization": f"Bearer {self.upstash_rest_token}"
                }
                # Use SETEX command: /setex/key/seconds/value
                # Value should be base64 encoded
                encoded_value = base64.b64encode(serialized).decode('utf-8')
                
                response = requests.post(
                    f"{self.upstash_rest_url}/setex/{key}/{ttl}/{encoded_value}",
                    headers=headers,
                    timeout=3
                )
                if response.status_code == 200:
                    return True
            except Exception as e:
                logger.debug(f"Upstash REST set error: {e}")
        
        # Fallback to standard Redis
        if self.use_redis and self.redis_client:
            try:
                serialized = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
                return True
            except Exception as e:
                logger.debug(f"Redis set error: {e}")
        return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if self.use_upstash_rest:
            try:
                headers = {"Authorization": f"Bearer {self.upstash_rest_token}"}
                requests.delete(
                    f"{self.upstash_rest_url}/del/{key}",
                    headers=headers,
                    timeout=3
                )
            except Exception as e:
                logger.debug(f"Upstash REST delete error: {e}")
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.debug(f"Redis delete error: {e}")
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern (e.g., 'user:*')"""
        # Note: Upstash REST API doesn't support KEYS command easily
        # This is mainly for standard Redis
        if self.use_redis and self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.debug(f"Redis clear pattern error: {e}")
    
    def cache_data(self, ttl: int = TTL_MEDIUM, show_spinner: bool = False):
        """Decorator for caching data with Redis/Upstash or Streamlit fallback"""
        if self.use_upstash_rest or self.use_redis:
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
                logger.info("Redis cache cleared")
            except Exception as e:
                logger.error(f"Redis flush error: {e}")
        
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
                logger.debug(f"Redis incr error: {e}")
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
