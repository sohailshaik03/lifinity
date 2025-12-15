# utils/performance_monitor.py
"""
Performance monitoring utilities
"""
from __future__ import annotations

import time
import streamlit as st
from functools import wraps
from typing import Any, Callable
from ..logger import logger


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    @staticmethod
    def time_function(func: Callable) -> Callable:
        """Decorator to measure function execution time"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                if elapsed > 1.0:  # Log slow functions (>1s)
                    logger.warning(f"⚠️ Slow function: {func.__name__} took {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"❌ Function {func.__name__} failed after {elapsed:.2f}s: {e}")
                raise
        return wrapper
    
    @staticmethod
    def log_query_time(query_name: str, start_time: float):
        """Log database query execution time"""
        elapsed = time.time() - start_time
        if elapsed > 0.5:  # Log slow queries (>500ms)
            logger.warning(f"🐌 Slow query: {query_name} took {elapsed:.2f}s")


# Singleton
perf_monitor = PerformanceMonitor()
