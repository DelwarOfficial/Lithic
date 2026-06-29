"""Graphify plugin adapter for the plugin system."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lithic_cli.graph.graphify_adapter import GraphifyAdapter
from lithic_cli.plugins import GraphProvider, PluginResult


class GraphifyPlugin(GraphProvider):
    """Plugin adapter for GraphifyAdapter."""
    
    def __init__(self, **config):
        self.config = config
        self._adapter = None
        
    @property
    def name(self) -> str:
        return "graphify"
    
    @property  
    def version(self) -> str:
        return "0.8.49"
    
    def _get_adapter(self, project_root: Path, output_dir: Path) -> GraphifyAdapter:
        """Get or create adapter instance."""
        if self._adapter is None or self._adapter.project_root != project_root:
            self._adapter = GraphifyAdapter(project_root, output_dir)
        return self._adapter
    
    def build_graph(self, project_root: Path, output_dir: Path) -> PluginResult[Path]:
        """Build project graph using Graphify."""
        try:
            adapter = self._get_adapter(project_root, output_dir)
            graph_path = adapter.build_graph(".")
            return PluginResult.ok(graph_path)
        except Exception as e:
            return PluginResult.error(f"Graph build failed: {e}")
    
    def query_graph(self, query: str, graph_path: Path) -> PluginResult[str]:
        """Query the graph with natural language."""
        try:
            # Extract project root from graph path
            project_root = graph_path.parent.parent if graph_path.name == "graph.json" else graph_path.parent
            output_dir = graph_path.parent
            
            adapter = self._get_adapter(project_root, output_dir)
            result = adapter.query(query)
            return PluginResult.ok(result)
        except Exception as e:
            return PluginResult.error(f"Graph query failed: {e}")
    
    def explain_concept(self, concept: str, graph_path: Path) -> PluginResult[str]:
        """Explain a concept using graph context."""
        try:
            project_root = graph_path.parent.parent if graph_path.name == "graph.json" else graph_path.parent
            output_dir = graph_path.parent
            
            adapter = self._get_adapter(project_root, output_dir)
            result = adapter.explain(concept)
            return PluginResult.ok(result)
        except Exception as e:
            return PluginResult.error(f"Concept explanation failed: {e}")
    
    def find_path(self, source: str, target: str, graph_path: Path) -> PluginResult[str]:
        """Find path between two concepts in graph."""
        try:
            project_root = graph_path.parent.parent if graph_path.name == "graph.json" else graph_path.parent
            output_dir = graph_path.parent
            
            adapter = self._get_adapter(project_root, output_dir)
            result = adapter.path_between(source, target)
            return PluginResult.ok(result)
        except Exception as e:
            return PluginResult.error(f"Path finding failed: {e}")
    
    def get_stats(self, graph_path: Path) -> PluginResult[dict[str, Any]]:
        """Get graph statistics."""
        try:
            project_root = graph_path.parent.parent if graph_path.name == "graph.json" else graph_path.parent
            output_dir = graph_path.parent
            
            adapter = self._get_adapter(project_root, output_dir)
            stats = adapter.stats()
            return PluginResult.ok(stats)
        except Exception as e:
            return PluginResult.error(f"Stats retrieval failed: {e}")
    
    def health_check(self) -> PluginResult[dict[str, Any]]:
        """Check if Graphify is available."""
        try:
            import shutil
            graphify_available = shutil.which("graphify") is not None
            
            # Try UV run fallback
            uv_available = False
            if not graphify_available:
                uv_available = shutil.which("uv") is not None
            
            return PluginResult.ok({
                "graphify_binary": graphify_available,
                "uv_fallback": uv_available,
                "available": graphify_available or uv_available,
                "adapter_config": self.config
            })
        except Exception as e:
            return PluginResult.error(f"Health check failed: {e}")