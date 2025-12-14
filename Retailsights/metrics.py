"""
Application metrics and monitoring
For observability in production environments
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import threading


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collect application metrics for monitoring
    In production, this would export to Prometheus, DataDog, etc.
    """
    
    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric (current value)"""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a value in histogram (for distributions)"""
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
            
            # Keep only last 1000 values to prevent memory issues
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
    
    def get_metrics(self) -> Dict[str, any]:
        """Get all current metrics"""
        with self._lock:
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {
                    k: {
                        'count': len(v),
                        'sum': sum(v),
                        'avg': sum(v) / len(v) if v else 0,
                        'min': min(v) if v else 0,
                        'max': max(v) if v else 0,
                    }
                    for k, v in self._histograms.items()
                }
            }
    
    @staticmethod
    def _make_key(name: str, labels: Dict[str, str] = None) -> str:
        """Create unique key from name and labels"""
        if not labels:
            return name
        label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# Global metrics instance
metrics = MetricsCollector()


# Common metric helpers
class Metrics:
    """Convenience wrapper for common metrics"""
    
    @staticmethod
    def track_request(endpoint: str, method: str = "GET"):
        """Track API/endpoint request"""
        metrics.increment_counter(
            "http_requests_total",
            labels={"endpoint": endpoint, "method": method}
        )
    
    @staticmethod
    def track_error(endpoint: str, error_type: str):
        """Track error occurrence"""
        metrics.increment_counter(
            "errors_total",
            labels={"endpoint": endpoint, "type": error_type}
        )
    
    @staticmethod
    def track_db_query(query_type: str, duration_ms: float):
        """Track database query"""
        metrics.increment_counter(
            "db_queries_total",
            labels={"type": query_type}
        )
        metrics.record_histogram(
            "db_query_duration_ms",
            duration_ms,
            labels={"type": query_type}
        )
    
    @staticmethod
    def track_cache_hit(cache_name: str, hit: bool):
        """Track cache hit/miss"""
        status = "hit" if hit else "miss"
        metrics.increment_counter(
            "cache_requests_total",
            labels={"cache": cache_name, "status": status}
        )
    
    @staticmethod
    def track_user_action(action: str, user_role: str):
        """Track user actions"""
        metrics.increment_counter(
            "user_actions_total",
            labels={"action": action, "role": user_role}
        )
    
    @staticmethod
    def set_active_users(count: int):
        """Set current active users gauge"""
        metrics.set_gauge("active_users", count)
    
    @staticmethod
    def set_database_connections(count: int):
        """Set current database connections"""
        metrics.set_gauge("db_connections_active", count)
