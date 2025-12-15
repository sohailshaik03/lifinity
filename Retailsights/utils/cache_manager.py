# utils/cache_manager.py
"""
Centralized caching utilities for performance optimization
"""
from __future__ import annotations

import streamlit as st
from functools import wraps
from typing import Any, Callable
import hashlib
import json


class CacheManager:
    """Manage application-wide caching"""
    
    # Cache TTLs in seconds
    TTL_SHORT = 60           # 1 minute - frequently changing data
    TTL_MEDIUM = 300         # 5 minutes - semi-static data
    TTL_LONG = 3600          # 1 hour - static reference data
    TTL_VERY_LONG = 86400    # 24 hours - rarely changing data
    
    @staticmethod
    def cache_data(ttl: int = TTL_MEDIUM, show_spinner: bool = False):
        """Decorator for caching data with configurable TTL"""
        return st.cache_data(ttl=ttl, show_spinner=show_spinner)
    
    @staticmethod
    def cache_resource(show_spinner: bool = False):
        """Decorator for caching resources (connections, models, etc.)"""
        return st.cache_resource(show_spinner=show_spinner)
    
    @staticmethod
    def clear_all_caches():
        """Clear all Streamlit caches"""
        st.cache_data.clear()
        st.cache_resource.clear()
    
    @staticmethod
    def get_cache_key(*args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


# Singleton instance
cache = CacheManager()
