"""Production monitoring and metrics collection."""

from __future__ import annotations

import psutil
import time
from collections import defaultdict
from threading import Lock
from typing import Any


class MetricsCollector:
    """Collects and aggregates system and application metrics."""
    
    def __init__(self):
        self._metrics = PrometheusMetrics()
        self._start_time = time.time()
    
    def get_system_metrics(self) -> dict[str, Any]:
        """Get current system metrics."""
        try:
            # Memory info
            memory = psutil.virtual_memory()
            
            # CPU info
            cpu_percent = psutil.cpu_percent()
            
            # Disk info
            disk = psutil.disk_usage('/')
            
            return {
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "used": disk.used,
                    "free_percent": (disk.free / disk.total) * 100
                },
                "uptime_seconds": time.time() - self._start_time
            }
        except Exception:
            return {}
    
    def get_application_metrics(self) -> dict[str, Any]:
        """Get application-specific metrics."""
        return {
            "requests_total": sum(self._metrics._counters.values()),
            "response_times": dict(self._metrics._histograms),
            "gauges": dict(self._metrics._gauges)
        }
    
    def get_summary(self) -> dict[str, Any]:
        """Get complete metrics summary."""
        return {
            "system": self.get_system_metrics(),
            "application": self.get_application_metrics(),
            "timestamp": time.time()
        }


class PrometheusMetrics:
    """Basic Prometheus-compatible metrics collector."""
    
    def __init__(self):
        self._counters: dict[str, int] = defaultdict(int)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}
        self._lock = Lock()
        self.start_time = time.time()
    
    def increment_counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        key = self._metric_key(name, labels or {})
        with self._lock:
            self._counters[key] += 1
    
    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a histogram observation."""
        key = self._metric_key(name, labels or {})
        with self._lock:
            self._histograms[key].append(value)
            # Keep only last 1000 observations to prevent memory growth
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
    
    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric value."""
        key = self._metric_key(name, labels or {})
        with self._lock:
            self._gauges[key] = value
    
    def _metric_key(self, name: str, labels: dict[str, str]) -> str:
        """Create a metric key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        # Counters
        for key, value in self._counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self._gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")
        
        # Histograms (simplified - just count and sum)
        for key, values in self._histograms.items():
            base_name = key.split('{')[0]
            lines.append(f"# TYPE {base_name} histogram")
            lines.append(f"{key.replace(base_name, f'{base_name}_count')} {len(values)}")
            lines.append(f"{key.replace(base_name, f'{base_name}_sum')} {sum(values):.6f}")
        
        # Built-in uptime gauge
        uptime = time.time() - self.start_time
        lines.append("# TYPE lithic_uptime_seconds gauge")
        lines.append(f"lithic_uptime_seconds {uptime:.0f}")
        
        return "\n".join(lines) + "\n"
    
    def get_stats(self) -> dict[str, Any]:
        """Get current metrics as a dictionary."""
        with self._lock:
            histogram_stats = {}
            for key, values in self._histograms.items():
                if values:
                    histogram_stats[key] = {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                    }
            
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": histogram_stats,
                "uptime_seconds": time.time() - self.start_time,
            }


# Global metrics instance
_metrics = PrometheusMetrics()


def get_metrics() -> PrometheusMetrics:
    """Get the global metrics collector."""
    return _metrics


def track_request_duration(operation: str, provider: str | None = None):
    """Decorator to track operation duration."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            labels = {"operation": operation}
            if provider:
                labels["provider"] = provider
            
            try:
                result = func(*args, **kwargs)
                _metrics.increment_counter("lithic_requests_total", {**labels, "status": "success"})
                return result
            except Exception as e:
                _metrics.increment_counter("lithic_requests_total", {**labels, "status": "error", "error_type": type(e).__name__})
                raise
            finally:
                duration = time.time() - start_time
                _metrics.observe_histogram("lithic_request_duration_seconds", duration, labels)
        
        return wrapper
    return decorator


# Global metrics collector instance  
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector