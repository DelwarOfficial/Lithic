"""Plugin system for extensible Lithic architecture."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

T = TypeVar('T')

class PluginResult[T]:
    """Standard result wrapper for plugin operations."""
    
    def __init__(self, success: bool, data: T | None = None, error: str | None = None):
        self.success = success
        self.data = data
        self.error = error
    
    @classmethod
    def ok(cls, data: T) -> PluginResult[T]:
        return cls(True, data, None)
    
    @classmethod
    def error(cls, error: str) -> PluginResult[T]:
        return cls(False, None, error)


class GraphProvider(ABC):
    """Abstract interface for graph providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property 
    @abstractmethod
    def version(self) -> str:
        """Provider version."""
        pass
    
    @abstractmethod
    def build_graph(self, project_root: Path, output_dir: Path) -> PluginResult[Path]:
        """Build project graph and return path to result."""
        pass
    
    @abstractmethod
    def query_graph(self, query: str, graph_path: Path) -> PluginResult[str]:
        """Query the graph with natural language."""
        pass
    
    @abstractmethod
    def explain_concept(self, concept: str, graph_path: Path) -> PluginResult[str]:
        """Explain a concept using graph context."""
        pass
    
    @abstractmethod
    def find_path(self, source: str, target: str, graph_path: Path) -> PluginResult[str]:
        """Find path between two concepts in graph."""
        pass
    
    @abstractmethod
    def get_stats(self, graph_path: Path) -> PluginResult[dict[str, Any]]:
        """Get graph statistics."""
        pass
    
    @abstractmethod
    def health_check(self) -> PluginResult[dict[str, Any]]:
        """Check if provider is healthy and available."""
        pass


class CompressionProvider(ABC):
    """Abstract interface for compression providers."""
    
    @property
    @abstractmethod 
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Provider version."""
        pass
    
    @abstractmethod
    def compress_text(self, text: str, context_type: str = "generic") -> PluginResult[str]:
        """Compress text with context-aware optimization."""
        pass
    
    @abstractmethod
    def compress_tool_output(self, output: str, tool_name: str = "unknown") -> PluginResult[str]:
        """Compress tool output with tool-specific rules."""
        pass
    
    @abstractmethod
    def get_compression_stats(self) -> PluginResult[dict[str, Any]]:
        """Get compression statistics."""
        pass
    
    @abstractmethod
    def health_check(self) -> PluginResult[dict[str, Any]]:
        """Check if provider is healthy and available."""
        pass


class ResponseProvider(ABC):
    """Abstract interface for response formatting providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Provider version."""
        pass
    
    @abstractmethod
    def shape_response(self, content: str, mode: str, context: dict[str, Any] = None) -> PluginResult[str]:
        """Shape response content according to mode and context."""
        pass
    
    @abstractmethod
    def get_available_modes(self) -> list[str]:
        """Get list of supported response modes."""
        pass
    
    @abstractmethod
    def health_check(self) -> PluginResult[dict[str, Any]]:
        """Check if provider is healthy and available."""
        pass


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """List of supported model names."""
        pass
    
    @abstractmethod
    def complete(self, messages: list[dict[str, str]], model: str, **kwargs) -> PluginResult[str]:
        """Generate completion using specified model."""
        pass
    
    @abstractmethod
    def health_check(self) -> PluginResult[dict[str, Any]]:
        """Check if provider is healthy and available."""
        pass


class PluginMetadata:
    """Plugin metadata and configuration."""
    
    def __init__(self, name: str, version: str, provider_type: str, 
                 entry_point: str, config: dict[str, Any] = None):
        self.name = name
        self.version = version
        self.provider_type = provider_type
        self.entry_point = entry_point
        self.config = config or {}
        self.enabled = True
        self.priority = 100  # Lower number = higher priority
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "provider_type": self.provider_type,
            "entry_point": self.entry_point,
            "config": self.config,
            "enabled": self.enabled,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginMetadata:
        meta = cls(
            name=data["name"],
            version=data["version"], 
            provider_type=data["provider_type"],
            entry_point=data["entry_point"],
            config=data.get("config", {})
        )
        meta.enabled = data.get("enabled", True)
        meta.priority = data.get("priority", 100)
        return meta