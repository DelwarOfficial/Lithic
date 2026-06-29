"""Advanced monitoring, alerting, and APM for production deployments."""

from __future__ import annotations

import asyncio
import logging
import os
import psutil
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from lithic_cli.monitoring import MetricsCollector

_log = logging.getLogger("lithic_cli.advanced_monitoring")


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertState(Enum):
    """Alert states."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Alert definition and state."""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    state: AlertState = AlertState.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def acknowledge(self, user: str = "system") -> None:
        """Acknowledge the alert."""
        self.state = AlertState.ACKNOWLEDGED
        self.acknowledged_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata["acknowledged_by"] = user
    
    def resolve(self, user: str = "system") -> None:
        """Resolve the alert."""
        self.state = AlertState.RESOLVED
        self.resolved_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata["resolved_by"] = user


class AlertRule(ABC):
    """Abstract alert rule interface."""
    
    @abstractmethod
    def evaluate(self, metrics: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate rule against metrics and return alert if triggered."""
        pass
    
    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique rule identifier."""
        pass


class ThresholdRule(AlertRule):
    """Simple threshold-based alert rule."""
    
    def __init__(self, rule_id: str, name: str, metric_path: str, 
                 threshold: float, operator: str = ">", 
                 severity: AlertSeverity = AlertSeverity.WARNING):
        self.id = rule_id
        self.name = name
        self.metric_path = metric_path
        self.threshold = threshold
        self.operator = operator
        self.severity = severity
    
    @property
    def rule_id(self) -> str:
        return self.id
    
    def evaluate(self, metrics: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate threshold rule."""
        try:
            # Navigate metric path (e.g., "system.memory.usage_percent")
            value = metrics
            for part in self.metric_path.split("."):
                value = value.get(part, {})
            
            if not isinstance(value, (int, float)):
                return None
            
            # Evaluate condition
            triggered = False
            if self.operator == ">":
                triggered = value > self.threshold
            elif self.operator == "<":
                triggered = value < self.threshold
            elif self.operator == ">=":
                triggered = value >= self.threshold
            elif self.operator == "<=":
                triggered = value <= self.threshold
            elif self.operator == "==":
                triggered = value == self.threshold
            elif self.operator == "!=":
                triggered = value != self.threshold
            
            if triggered:
                return Alert(
                    id=f"{self.id}-{int(time.time())}",
                    name=self.name,
                    description=f"{self.metric_path} {self.operator} {self.threshold} (current: {value})",
                    severity=self.severity,
                    metadata={
                        "rule_id": self.id,
                        "metric_path": self.metric_path,
                        "threshold": self.threshold,
                        "operator": self.operator,
                        "current_value": value
                    }
                )
            
            return None
            
        except Exception as e:
            _log.error(f"Error evaluating rule {self.id}: {e}")
            return None


class RateRule(AlertRule):
    """Rate-based alert rule (change over time)."""
    
    def __init__(self, rule_id: str, name: str, metric_path: str,
                 rate_threshold: float, time_window: int = 300,
                 severity: AlertSeverity = AlertSeverity.WARNING):
        self.id = rule_id
        self.name = name
        self.metric_path = metric_path
        self.rate_threshold = rate_threshold
        self.time_window = time_window  # seconds
        self.severity = severity
        self._history: List[tuple[datetime, float]] = []
    
    @property
    def rule_id(self) -> str:
        return self.id
    
    def evaluate(self, metrics: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate rate-based rule."""
        try:
            # Get current value
            value = metrics
            for part in self.metric_path.split("."):
                value = value.get(part, {})
            
            if not isinstance(value, (int, float)):
                return None
            
            now = datetime.now()
            self._history.append((now, value))
            
            # Clean old entries
            cutoff = now - timedelta(seconds=self.time_window)
            self._history = [(t, v) for t, v in self._history if t > cutoff]
            
            if len(self._history) < 2:
                return None
            
            # Calculate rate
            oldest = self._history[0]
            newest = self._history[-1]
            time_diff = (newest[0] - oldest[0]).total_seconds()
            value_diff = newest[1] - oldest[1]
            
            if time_diff == 0:
                return None
            
            rate = value_diff / time_diff
            
            if abs(rate) > self.rate_threshold:
                return Alert(
                    id=f"{self.id}-{int(time.time())}",
                    name=self.name,
                    description=f"{self.metric_path} rate {rate:.2f}/sec exceeds threshold {self.rate_threshold}/sec",
                    severity=self.severity,
                    metadata={
                        "rule_id": self.id,
                        "metric_path": self.metric_path,
                        "rate_threshold": self.rate_threshold,
                        "current_rate": rate,
                        "time_window": self.time_window
                    }
                )
            
            return None
            
        except Exception as e:
            _log.error(f"Error evaluating rate rule {self.id}: {e}")
            return None


class AlertChannel(ABC):
    """Abstract alert notification channel."""
    
    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert notification."""
        pass
    
    @property
    @abstractmethod
    def channel_id(self) -> str:
        """Unique channel identifier."""
        pass


class LoggerChannel(AlertChannel):
    """Log-based alert channel."""
    
    def __init__(self, logger_name: str = "lithic_cli.alerts"):
        self.logger = logging.getLogger(logger_name)
    
    @property
    def channel_id(self) -> str:
        return "logger"
    
    async def send_alert(self, alert: Alert) -> bool:
        """Log the alert."""
        try:
            level = {
                AlertSeverity.INFO: logging.INFO,
                AlertSeverity.WARNING: logging.WARNING,
                AlertSeverity.ERROR: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(alert.severity, logging.WARNING)
            
            self.logger.log(level, f"ALERT [{alert.severity.value.upper()}] {alert.name}: {alert.description}")
            return True
            
        except Exception as e:
            _log.error(f"Failed to log alert: {e}")
            return False


class FileChannel(AlertChannel):
    """File-based alert channel."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def channel_id(self) -> str:
        return f"file:{self.file_path}"
    
    async def send_alert(self, alert: Alert) -> bool:
        """Write alert to file."""
        try:
            alert_data = {
                "timestamp": alert.created_at.isoformat(),
                "id": alert.id,
                "name": alert.name,
                "description": alert.description,
                "severity": alert.severity.value,
                "state": alert.state.value,
                "metadata": alert.metadata
            }
            
            with self.file_path.open("a") as f:
                f.write(f"{alert_data}\n")
            
            return True
            
        except Exception as e:
            _log.error(f"Failed to write alert to file: {e}")
            return False


class WebhookChannel(AlertChannel):
    """HTTP webhook alert channel."""
    
    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}
    
    @property
    def channel_id(self) -> str:
        return f"webhook:{self.webhook_url}"
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via HTTP webhook."""
        try:
            import httpx
            
            payload = {
                "alert": {
                    "id": alert.id,
                    "name": alert.name,
                    "description": alert.description,
                    "severity": alert.severity.value,
                    "state": alert.state.value,
                    "created_at": alert.created_at.isoformat(),
                    "metadata": alert.metadata
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
                
                if 200 <= response.status_code < 300:
                    return True
                else:
                    _log.warning(f"Webhook returned status {response.status_code}")
                    return False
                    
        except ImportError:
            _log.error("httpx not installed, webhook channel unavailable")
            return False
        except Exception as e:
            _log.error(f"Failed to send webhook alert: {e}")
            return False


class AlertManager:
    """Manages alert rules, evaluation, and notifications."""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.channels: Dict[str, AlertChannel] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self._evaluation_task: Optional[asyncio.Task] = None
        self._running = False
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add alert rule."""
        self.rules[rule.rule_id] = rule
        _log.info(f"Added alert rule: {rule.rule_id}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove alert rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            _log.info(f"Removed alert rule: {rule_id}")
            return True
        return False
    
    def add_channel(self, channel: AlertChannel) -> None:
        """Add notification channel."""
        self.channels[channel.channel_id] = channel
        _log.info(f"Added alert channel: {channel.channel_id}")
    
    def remove_channel(self, channel_id: str) -> bool:
        """Remove notification channel."""
        if channel_id in self.channels:
            del self.channels[channel_id]
            _log.info(f"Removed alert channel: {channel_id}")
            return True
        return False
    
    async def evaluate_rules(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Evaluate all rules against current metrics."""
        new_alerts = []
        
        for rule in self.rules.values():
            try:
                alert = rule.evaluate(metrics)
                if alert:
                    # Check if this is a duplicate (same rule triggered recently)
                    recent_alerts = [
                        a for a in self.active_alerts.values()
                        if a.metadata.get("rule_id") == rule.rule_id
                        and (datetime.now() - a.created_at).total_seconds() < 300  # 5 min
                    ]
                    
                    if not recent_alerts:
                        new_alerts.append(alert)
                        self.active_alerts[alert.id] = alert
                        self.alert_history.append(alert)
                        
                        # Send notifications
                        await self._send_alert_notifications(alert)
                        
            except Exception as e:
                _log.error(f"Error evaluating rule {rule.rule_id}: {e}")
        
        return new_alerts
    
    async def _send_alert_notifications(self, alert: Alert) -> None:
        """Send alert to all configured channels."""
        for channel in self.channels.values():
            try:
                success = await channel.send_alert(alert)
                if not success:
                    _log.warning(f"Failed to send alert {alert.id} to channel {channel.channel_id}")
            except Exception as e:
                _log.error(f"Error sending alert to {channel.channel_id}: {e}")
    
    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Acknowledge an active alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledge(user)
            _log.info(f"Alert {alert_id} acknowledged by {user}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str, user: str = "system") -> bool:
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolve(user)
            del self.active_alerts[alert_id]  # Remove from active
            _log.info(f"Alert {alert_id} resolved by {user}")
            return True
        return False
    
    async def start_monitoring(self, metrics_collector: MetricsCollector, 
                             evaluation_interval: int = 60) -> None:
        """Start continuous alert monitoring."""
        if self._running:
            return
        
        self._running = True
        _log.info(f"Starting alert monitoring with {evaluation_interval}s interval")
        
        self._evaluation_task = asyncio.create_task(
            self._monitoring_loop(metrics_collector, evaluation_interval)
        )
    
    async def stop_monitoring(self) -> None:
        """Stop alert monitoring."""
        if self._evaluation_task:
            self._evaluation_task.cancel()
            try:
                await self._evaluation_task
            except asyncio.CancelledError:
                pass
            self._evaluation_task = None
        
        self._running = False
        _log.info("Stopped alert monitoring")
    
    async def _monitoring_loop(self, metrics_collector: MetricsCollector, 
                              interval: int) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Collect current metrics
                metrics = {
                    "system": metrics_collector.get_system_metrics(),
                    "application": metrics_collector.get_application_metrics()
                }
                
                # Evaluate rules
                new_alerts = await self.evaluate_rules(metrics)
                
                if new_alerts:
                    _log.info(f"Generated {len(new_alerts)} new alerts")
                
                # Cleanup old resolved alerts from history
                cutoff = datetime.now() - timedelta(days=7)
                self.alert_history = [
                    a for a in self.alert_history
                    if a.state != AlertState.RESOLVED or a.resolved_at > cutoff
                ]
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                _log.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        active_by_severity = {}
        for severity in AlertSeverity:
            active_by_severity[severity.value] = sum(
                1 for alert in self.active_alerts.values()
                if alert.severity == severity
            )
        
        return {
            "active_alerts": len(self.active_alerts),
            "total_rules": len(self.rules),
            "total_channels": len(self.channels),
            "alerts_last_24h": sum(
                1 for alert in self.alert_history
                if (datetime.now() - alert.created_at).total_seconds() < 86400
            ),
            "active_by_severity": active_by_severity,
            "monitoring_active": self._running
        }
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())


class APMCollector:
    """Application Performance Monitoring collector."""
    
    def __init__(self):
        self.traces: List[Dict[str, Any]] = []
        self.spans: Dict[str, Dict[str, Any]] = {}
        self.error_counts: Dict[str, int] = {}
        self.response_times: Dict[str, List[float]] = {}
        self._start_time = time.time()
    
    def start_trace(self, trace_id: str, operation: str) -> Dict[str, Any]:
        """Start a new trace."""
        trace = {
            "trace_id": trace_id,
            "operation": operation,
            "start_time": time.time(),
            "spans": [],
            "status": "active"
        }
        
        self.traces.append(trace)
        return trace
    
    def start_span(self, span_id: str, operation: str, parent_span: str = None) -> Dict[str, Any]:
        """Start a new span."""
        span = {
            "span_id": span_id,
            "operation": operation,
            "parent_span": parent_span,
            "start_time": time.time(),
            "tags": {},
            "status": "active"
        }
        
        self.spans[span_id] = span
        return span
    
    def finish_span(self, span_id: str, status: str = "success", tags: Dict[str, Any] = None) -> None:
        """Finish a span."""
        if span_id in self.spans:
            span = self.spans[span_id]
            span["end_time"] = time.time()
            span["duration"] = span["end_time"] - span["start_time"]
            span["status"] = status
            if tags:
                span["tags"].update(tags)
            
            # Track response times by operation
            operation = span["operation"]
            if operation not in self.response_times:
                self.response_times[operation] = []
            
            self.response_times[operation].append(span["duration"])
            
            # Keep only recent response times
            if len(self.response_times[operation]) > 1000:
                self.response_times[operation] = self.response_times[operation][-500:]
            
            # Track errors
            if status == "error":
                self.error_counts[operation] = self.error_counts.get(operation, 0) + 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        metrics = {
            "total_traces": len(self.traces),
            "active_spans": sum(1 for s in self.spans.values() if s["status"] == "active"),
            "uptime_seconds": time.time() - self._start_time,
            "operations": {}
        }
        
        for operation, times in self.response_times.items():
            if times:
                metrics["operations"][operation] = {
                    "count": len(times),
                    "avg_response_time": sum(times) / len(times),
                    "min_response_time": min(times),
                    "max_response_time": max(times),
                    "p95_response_time": sorted(times)[int(len(times) * 0.95)] if times else 0,
                    "error_count": self.error_counts.get(operation, 0),
                    "error_rate": self.error_counts.get(operation, 0) / len(times)
                }
        
        return metrics


def create_default_alert_manager() -> AlertManager:
    """Create alert manager with default rules and channels."""
    manager = AlertManager()
    
    # Add default rules
    manager.add_rule(ThresholdRule(
        "high_memory", "High Memory Usage", "system.memory.percent",
        85.0, ">", AlertSeverity.WARNING
    ))
    
    manager.add_rule(ThresholdRule(
        "critical_memory", "Critical Memory Usage", "system.memory.percent",
        95.0, ">", AlertSeverity.CRITICAL
    ))
    
    manager.add_rule(ThresholdRule(
        "high_cpu", "High CPU Usage", "system.cpu.percent",
        80.0, ">", AlertSeverity.WARNING
    ))
    
    manager.add_rule(ThresholdRule(
        "low_disk_space", "Low Disk Space", "system.disk.free_percent",
        10.0, "<", AlertSeverity.ERROR
    ))
    
    # Add default channels
    manager.add_channel(LoggerChannel())
    
    # Add file channel if configured
    alerts_dir = os.getenv("LITHIC_ALERTS_DIR")
    if alerts_dir:
        manager.add_channel(FileChannel(Path(alerts_dir) / "alerts.jsonl"))
    
    # Add webhook if configured
    webhook_url = os.getenv("LITHIC_ALERT_WEBHOOK")
    if webhook_url:
        manager.add_channel(WebhookChannel(webhook_url))
    
    return manager


# Global instances
_alert_manager: AlertManager | None = None
_apm_collector: APMCollector | None = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = create_default_alert_manager()
    return _alert_manager


def get_apm_collector() -> APMCollector:
    """Get or create global APM collector."""
    global _apm_collector
    if _apm_collector is None:
        _apm_collector = APMCollector()
    return _apm_collector