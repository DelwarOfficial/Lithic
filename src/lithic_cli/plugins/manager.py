"""Plugin discovery, loading, and lifecycle management."""

from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type, TypeVar, Optional

from lithic_cli.plugins import (
    GraphProvider, CompressionProvider, ResponseProvider, LLMProvider,
    PluginMetadata, PluginResult
)

_log = logging.getLogger("lithic_cli.plugins")

T = TypeVar('T', GraphProvider, CompressionProvider, ResponseProvider, LLMProvider)


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle."""
    
    def __init__(self, plugin_dirs: List[Path] = None):
        self.plugin_dirs = plugin_dirs or [Path.cwd() / "plugins"]
        self._plugins: Dict[str, Dict[str, Any]] = {
            "graph": {},
            "compression": {},
            "response": {},
            "llm": {}
        }
        self._instances: Dict[str, Any] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
    
    def discover_plugins(self) -> Dict[str, List[PluginMetadata]]:
        """Discover all available plugins from plugin directories."""
        discovered = {
            "graph": [],
            "compression": [], 
            "response": [],
            "llm": []
        }
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
                
            for plugin_path in plugin_dir.iterdir():
                if plugin_path.is_dir() and (plugin_path / "plugin.json").exists():
                    try:
                        metadata = self._load_plugin_metadata(plugin_path / "plugin.json")
                        if metadata.provider_type in discovered:
                            discovered[metadata.provider_type].append(metadata)
                            self._metadata[metadata.name] = metadata
                    except Exception as e:
                        _log.warning(f"Failed to load plugin metadata from {plugin_path}: {e}")
        
        return discovered
    
    def _load_plugin_metadata(self, metadata_path: Path) -> PluginMetadata:
        """Load plugin metadata from plugin.json file."""
        data = json.loads(metadata_path.read_text())
        return PluginMetadata.from_dict(data)
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load and instantiate a specific plugin."""
        if plugin_name not in self._metadata:
            _log.error(f"Plugin {plugin_name} not found in discovered plugins")
            return False
        
        metadata = self._metadata[plugin_name]
        if not metadata.enabled:
            _log.info(f"Plugin {plugin_name} is disabled")
            return False
        
        try:
            # Import the plugin module
            module_path, class_name = metadata.entry_point.split(":")
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            
            # Instantiate with config
            instance = plugin_class(**metadata.config)
            
            # Store instance
            self._instances[plugin_name] = instance
            self._plugins[metadata.provider_type][plugin_name] = instance
            
            _log.info(f"Loaded plugin {plugin_name} v{metadata.version}")
            return True
            
        except Exception as e:
            _log.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def load_all_plugins(self) -> Dict[str, int]:
        """Load all discovered and enabled plugins."""
        self.discover_plugins()
        
        loaded_count = {"graph": 0, "compression": 0, "response": 0, "llm": 0}
        
        # Sort by priority (lower number = higher priority)
        for provider_type in loaded_count.keys():
            plugins = [(name, meta) for name, meta in self._metadata.items() 
                      if meta.provider_type == provider_type]
            plugins.sort(key=lambda x: x[1].priority)
            
            for plugin_name, _ in plugins:
                if self.load_plugin(plugin_name):
                    loaded_count[provider_type] += 1
        
        return loaded_count
    
    def get_provider(self, provider_type: str, name: str = None) -> Any | None:
        """Get a specific provider instance or the highest priority one."""
        if provider_type not in self._plugins:
            return None
        
        providers = self._plugins[provider_type]
        if not providers:
            return None
        
        if name:
            return providers.get(name)
        
        # Return highest priority (lowest number) provider
        sorted_providers = sorted(
            providers.items(),
            key=lambda x: self._metadata[x[0]].priority
        )
        return sorted_providers[0][1] if sorted_providers else None
    
    def get_graph_provider(self, name: str = None) -> GraphProvider | None:
        """Get graph provider instance."""
        return self.get_provider("graph", name)
    
    def get_compression_provider(self, name: str = None) -> CompressionProvider | None:
        """Get compression provider instance."""  
        return self.get_provider("compression", name)
    
    def get_response_provider(self, name: str = None) -> ResponseProvider | None:
        """Get response provider instance."""
        return self.get_provider("response", name)
    
    def get_llm_provider(self, name: str = None) -> LLMProvider | None:
        """Get LLM provider instance."""
        return self.get_provider("llm", name)
    
    def list_providers(self, provider_type: str = None) -> Dict[str, List[str]]:
        """List all available providers by type."""
        if provider_type:
            return {provider_type: list(self._plugins.get(provider_type, {}).keys())}
        
        return {
            ptype: list(providers.keys()) 
            for ptype, providers in self._plugins.items()
        }
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Run health checks on all loaded plugins."""
        results = {}
        
        for provider_type, providers in self._plugins.items():
            results[provider_type] = {}
            for name, instance in providers.items():
                try:
                    health_result = instance.health_check()
                    results[provider_type][name] = {
                        "healthy": health_result.success,
                        "data": health_result.data,
                        "error": health_result.error
                    }
                except Exception as e:
                    results[provider_type][name] = {
                        "healthy": False,
                        "error": str(e)
                    }
        
        return results
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a specific plugin (useful for development)."""
        if plugin_name in self._instances:
            # Remove from instances and provider lists
            metadata = self._metadata[plugin_name]
            self._plugins[metadata.provider_type].pop(plugin_name, None)
            self._instances.pop(plugin_name, None)
        
        return self.load_plugin(plugin_name)
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin."""
        if plugin_name not in self._instances:
            return False
        
        metadata = self._metadata[plugin_name]
        self._plugins[metadata.provider_type].pop(plugin_name, None)
        self._instances.pop(plugin_name, None)
        
        _log.info(f"Unloaded plugin {plugin_name}")
        return True
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded plugins."""
        return {
            "discovered": len(self._metadata),
            "loaded": len(self._instances),
            "by_type": {
                ptype: len(providers) 
                for ptype, providers in self._plugins.items()
            },
            "enabled": sum(1 for meta in self._metadata.values() if meta.enabled),
            "disabled": sum(1 for meta in self._metadata.values() if not meta.enabled)
        }


# Global plugin manager instance
_plugin_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """Get or create the global plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
        _plugin_manager.load_all_plugins()
    return _plugin_manager