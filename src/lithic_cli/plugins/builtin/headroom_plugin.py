"""Headroom compression plugin adapter."""

from __future__ import annotations

from typing import Any

from lithic_cli.compression.headroom_adapter import HeadroomAdapter
from lithic_cli.plugins import CompressionProvider, PluginResult


class HeadroomPlugin(CompressionProvider):
    """Plugin adapter for HeadroomAdapter."""
    
    def __init__(self, cache_size: int = 1000, **config):
        self.config = config
        self.cache_size = cache_size
        self._adapter = HeadroomAdapter(cache_size=cache_size)
    
    @property
    def name(self) -> str:
        return "headroom"
    
    @property
    def version(self) -> str:
        return "0.27.0"
    
    def compress_text(self, text: str, context_type: str = "generic") -> PluginResult[str]:
        """Compress text with context-aware optimization."""
        try:
            # Use context_type as label for headroom
            result = self._adapter.compress_text(text, label=context_type)
            return PluginResult.ok(result)
        except Exception as e:
            return PluginResult.error(f"Text compression failed: {e}")
    
    def compress_tool_output(self, output: str, tool_name: str = "unknown") -> PluginResult[str]:
        """Compress tool output with tool-specific rules."""
        try:
            # Map tool names to appropriate compression strategies
            tool_config = self._get_tool_config(tool_name)
            result = self._adapter.compress_tool_output(output, **tool_config)
            return PluginResult.ok(result)
        except Exception as e:
            return PluginResult.error(f"Tool output compression failed: {e}")
    
    def _get_tool_config(self, tool_name: str) -> dict[str, Any]:
        """Get compression configuration for specific tools."""
        tool_configs = {
            "git": {"max_chars": 50000, "preserve_structure": True},
            "pytest": {"max_chars": 30000, "preserve_errors": True},
            "ruff": {"max_chars": 20000, "preserve_line_numbers": True},
            "mypy": {"max_chars": 25000, "preserve_errors": True},
            "ls": {"max_chars": 10000, "tabular_format": True},
            "find": {"max_chars": 15000, "preserve_paths": True},
            "grep": {"max_chars": 40000, "preserve_matches": True},
            "default": {"max_chars": 100000}
        }
        
        return tool_configs.get(tool_name, tool_configs["default"])
    
    def get_compression_stats(self) -> PluginResult[dict[str, Any]]:
        """Get compression statistics."""
        try:
            stats = self._adapter.stats()
            return PluginResult.ok(stats)
        except Exception as e:
            return PluginResult.error(f"Stats retrieval failed: {e}")
    
    def health_check(self) -> PluginResult[dict[str, Any]]:
        """Check if Headroom is available and functional."""
        try:
            # Test compression with small input
            test_text = "This is a test compression input to verify functionality."
            result = self._adapter.compress_text(test_text)
            
            # Check if headroom is actually available
            headroom_available = hasattr(self._adapter, '_headroom_available') and self._adapter._headroom_available
            
            return PluginResult.ok({
                "headroom_available": headroom_available,
                "fallback_compression": not headroom_available,
                "test_compression_works": len(result) <= len(test_text),
                "cache_size": self.cache_size,
                "cache_stats": self._adapter.stats()
            })
        except Exception as e:
            return PluginResult.error(f"Health check failed: {e}")