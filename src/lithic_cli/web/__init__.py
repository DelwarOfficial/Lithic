"""Web dashboard and API for Lithic CLI."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from lithic_cli.caching import get_cache
from lithic_cli.config import AgentConfig
from lithic_cli.graph.backends import get_default_backend
from lithic_cli.microservices import get_service_manager
from lithic_cli.monitoring import get_metrics_collector
from lithic_cli.plugins.manager import get_plugin_manager

_log = logging.getLogger("lithic_cli.web")

# Web framework detection and configuration
try:
    from fastapi import FastAPI, HTTPException, WebSocket
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
    _has_fastapi = True
except ImportError:
    _log.warning("FastAPI not installed, web dashboard disabled")
    _has_fastapi = False
    BaseModel = None
    FastAPI = None


if _has_fastapi:
    class ProjectInfo(BaseModel):
        """Project information model."""
        name: str
        path: str
        graph_exists: bool
        node_count: int
        edge_count: int
        last_indexed: datetime | None
    
    class SystemStatus(BaseModel):
        """System status model."""
        healthy: bool
        uptime_seconds: float
        memory_usage_mb: float
        cache_hit_rate: float
        plugins_loaded: int
        services_running: int
    
    class QueryRequest(BaseModel):
        """Query request model."""
        question: str
        context: dict[str, Any] | None = None
    
    class CompressionRequest(BaseModel):
        """Compression request model."""
        text: str
        context_type: str = "generic"


class WebDashboard:
    """Web dashboard server for Lithic CLI."""
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig.from_env()
        self.app = None
        self._server_task = None
        self._websocket_clients = []
        
        if _has_fastapi:
            self._setup_fastapi_app()
    
    def _setup_fastapi_app(self) -> None:
        """Setup FastAPI application with routes."""
        self.app = FastAPI(
            title="Lithic CLI Dashboard",
            description="Web dashboard and API for Lithic CLI",
            version="0.2.0"
        )
        
        # Static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Main dashboard page."""
            return self._get_dashboard_html()
        
        @self.app.get("/api/status", response_model=SystemStatus)
        async def get_status():
            """Get system status."""
            return await self._get_system_status()
        
        @self.app.get("/api/projects", response_model=list[ProjectInfo])
        async def list_projects():
            """List available projects."""
            return await self._list_projects()
        
        @self.app.get("/api/projects/{project_id}")
        async def get_project(project_id: str):
            """Get project details."""
            return await self._get_project_details(project_id)
        
        @self.app.post("/api/query")
        async def query_graph(request: QueryRequest):
            """Query the graph."""
            try:
                # Use orchestrator for query
                from lithic_cli.orchestrator import Orchestrator
                orchestrator = Orchestrator(self.config)
                result = orchestrator.ask(request.question)
                
                return {
                    "success": True,
                    "result": result,
                    "timestamp": datetime.now()
                }
            except Exception as e:
                _log.error(f"Query error: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e
        
        @self.app.post("/api/compress")
        async def compress_text(request: CompressionRequest):
            """Compress text content."""
            try:
                plugin_manager = get_plugin_manager()
                compression_provider = plugin_manager.get_compression_provider()
                
                if not compression_provider:
                    raise HTTPException(status_code=503, detail="No compression provider available")
                
                result = compression_provider.compress_text(
                    request.text, 
                    request.context_type
                )
                
                if result.success:
                    return {
                        "success": True,
                        "compressed_text": result.data,
                        "original_length": len(request.text),
                        "compressed_length": len(result.data),
                        "compression_ratio": len(result.data) / len(request.text)
                    }
                else:
                    raise HTTPException(status_code=500, detail=result.error)
                    
            except Exception as e:
                _log.error(f"Compression error: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e
        
        @self.app.get("/api/cache/stats")
        async def get_cache_stats():
            """Get cache statistics."""
            try:
                cache = get_cache()
                return cache.stats()
            except Exception as e:
                _log.error(f"Cache stats error: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e
        
        @self.app.get("/api/plugins")
        async def list_plugins():
            """List loaded plugins."""
            try:
                plugin_manager = get_plugin_manager()
                return {
                    "providers": plugin_manager.list_providers(),
                    "stats": plugin_manager.get_plugin_stats(),
                    "health": plugin_manager.health_check_all()
                }
            except Exception as e:
                _log.error(f"Plugins error: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e
        
        @self.app.get("/api/services")
        async def list_services():
            """List microservices."""
            try:
                service_manager = get_service_manager()
                return {
                    "services": [
                        {
                            "name": f"{s.config.name}-{s.instance_id}",
                            "type": s.config.service_type.value,
                            "status": s.status,
                            "health": s.health_status,
                            "pid": s.pid,
                            "started_at": s.started_at,
                            "host": s.config.host,
                            "port": s.config.port
                        }
                        for s in service_manager.registry.list_all()
                    ],
                    "summary": service_manager.registry.health_summary(),
                    "stats": service_manager.get_service_stats()
                }
            except Exception as e:
                _log.error(f"Services error: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get system metrics."""
            try:
                metrics = get_metrics_collector()
                return metrics.get_summary()
            except Exception as e:
                _log.error(f"Metrics error: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e
        
        @self.app.websocket("/ws/events")
        async def websocket_events(websocket: WebSocket):
            """WebSocket for real-time events."""
            await websocket.accept()
            self._websocket_clients.append(websocket)
            
            try:
                # Send initial status
                await websocket.send_json({
                    "type": "status",
                    "data": await self._get_system_status()
                })
                
                # Keep connection alive and send periodic updates
                while True:
                    await asyncio.sleep(10)
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                _log.error(f"WebSocket error: {e}")
            finally:
                if websocket in self._websocket_clients:
                    self._websocket_clients.remove(websocket)
    
    async def _get_system_status(self) -> SystemStatus:
        """Get comprehensive system status."""
        try:
            # Cache stats
            cache = get_cache()
            cache_stats = cache.stats()
            
            # Plugin stats
            plugin_manager = get_plugin_manager()
            plugin_stats = plugin_manager.get_plugin_stats()
            
            # Service stats
            service_manager = get_service_manager()
            service_stats = service_manager.get_service_stats()
            
            # Metrics
            metrics = get_metrics_collector()
            system_metrics = metrics.get_system_metrics()
            
            return SystemStatus(
                healthy=True,  # TODO: Aggregate health checks
                uptime_seconds=system_metrics.get("uptime_seconds", 0),
                memory_usage_mb=system_metrics.get("memory_usage_mb", 0),
                cache_hit_rate=cache_stats.get("hit_rate", 0),
                plugins_loaded=plugin_stats.get("loaded", 0),
                services_running=service_stats.get("running_processes", 0)
            )
            
        except Exception as e:
            _log.error(f"Failed to get system status: {e}")
            return SystemStatus(
                healthy=False,
                uptime_seconds=0,
                memory_usage_mb=0,
                cache_hit_rate=0,
                plugins_loaded=0,
                services_running=0
            )
    
    async def _list_projects(self) -> list[ProjectInfo]:
        """List available projects."""
        # For now, just return current project
        try:
            backend = get_default_backend()
            stats = backend.get_stats("current")
            
            return [ProjectInfo(
                name="current",
                path=str(self.config.project_root),
                graph_exists=stats.get("nodes", 0) > 0,
                node_count=stats.get("nodes", 0),
                edge_count=stats.get("edges", 0),
                last_indexed=datetime.now()  # TODO: Track actual indexing time
            )]
            
        except Exception as e:
            _log.error(f"Failed to list projects: {e}")
            return []
    
    async def _get_project_details(self, project_id: str) -> dict[str, Any]:
        """Get detailed project information."""
        try:
            backend = get_default_backend()
            stats = backend.get_stats(project_id)
            
            return {
                "id": project_id,
                "stats": stats,
                "health": backend.health_check()
            }
            
        except Exception as e:
            _log.error(f"Failed to get project details: {e}")
            raise HTTPException(status_code=404, detail="Project not found") from e
    
    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML content."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Lithic CLI Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: #f5f5f5; 
                }
                .header { 
                    background: #fff; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin-bottom: 20px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .grid { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 20px; 
                }
                .card { 
                    background: #fff; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                }
                .status-healthy { color: #28a745; }
                .status-warning { color: #ffc107; }
                .status-error { color: #dc3545; }
                .query-box { 
                    width: 100%; 
                    padding: 10px; 
                    border: 1px solid #ddd; 
                    border-radius: 4px; 
                    margin-bottom: 10px; 
                }
                .btn { 
                    background: #007bff; 
                    color: white; 
                    border: none; 
                    padding: 10px 20px; 
                    border-radius: 4px; 
                    cursor: pointer; 
                }
                .btn:hover { background: #0056b3; }
                #status { margin-top: 10px; }
                .metric { 
                    display: flex; 
                    justify-content: space-between; 
                    margin: 10px 0; 
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔬 Lithic CLI Dashboard</h1>
                <p>Graph-first unified coding agent with production-grade architecture</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>System Status</h3>
                    <div id="system-status">Loading...</div>
                </div>
                
                <div class="card">
                    <h3>Quick Query</h3>
                    <textarea class="query-box" id="query-input" placeholder="Ask about your codebase..."></textarea>
                    <button class="btn" onclick="submitQuery()">Query Graph</button>
                    <div id="query-result"></div>
                </div>
                
                <div class="card">
                    <h3>Cache Performance</h3>
                    <div id="cache-stats">Loading...</div>
                </div>
                
                <div class="card">
                    <h3>Plugins</h3>
                    <div id="plugin-info">Loading...</div>
                </div>
                
                <div class="card">
                    <h3>Microservices</h3>
                    <div id="service-info">Loading...</div>
                </div>
                
                <div class="card">
                    <h3>Metrics</h3>
                    <div id="metrics-info">Loading...</div>
                </div>
            </div>
            
            <script>
                async function loadStatus() {
                    try {
                        const response = await fetch('/api/status');
                        const status = await response.json();
                        
                        document.getElementById('system-status').innerHTML = `
                            <div class="metric">
                                <span>Health:</span>
                                <span class="${status.healthy ? 'status-healthy' : 'status-error'}">
                                    ${status.healthy ? '✓ Healthy' : '✗ Unhealthy'}
                                </span>
                            </div>
                            <div class="metric">
                                <span>Uptime:</span>
                                <span>${Math.round(status.uptime_seconds / 60)} minutes</span>
                            </div>
                            <div class="metric">
                                <span>Memory:</span>
                                <span>${Math.round(status.memory_usage_mb)} MB</span>
                            </div>
                            <div class="metric">
                                <span>Cache Hit Rate:</span>
                                <span>${(status.cache_hit_rate * 100).toFixed(1)}%</span>
                            </div>
                        `;
                    } catch (error) {
                        document.getElementById('system-status').innerHTML = 
                            '<span class="status-error">Failed to load status</span>';
                    }
                }
                
                async function loadCacheStats() {
                    try {
                        const response = await fetch('/api/cache/stats');
                        const stats = await response.json();
                        
                        document.getElementById('cache-stats').innerHTML = `
                            <div class="metric">
                                <span>Hit Rate:</span>
                                <span>${(stats.hit_rate * 100).toFixed(1)}%</span>
                            </div>
                            <div class="metric">
                                <span>L1 Hits:</span>
                                <span>${stats.hits_l1}</span>
                            </div>
                            <div class="metric">
                                <span>L2 Available:</span>
                                <span class="${stats.l2_available ? 'status-healthy' : 'status-warning'}">
                                    ${stats.l2_available ? '✓ Yes' : '✗ No'}
                                </span>
                            </div>
                        `;
                    } catch (error) {
                        document.getElementById('cache-stats').innerHTML = 
                            '<span class="status-error">Failed to load cache stats</span>';
                    }
                }
                
                async function loadPlugins() {
                    try {
                        const response = await fetch('/api/plugins');
                        const plugins = await response.json();
                        
                        let html = '';
                        for (const [type, providers] of Object.entries(plugins.providers)) {
                            html += `<div class="metric">
                                <span>${type}:</span>
                                <span>${providers.length} loaded</span>
                            </div>`;
                        }
                        
                        document.getElementById('plugin-info').innerHTML = html;
                    } catch (error) {
                        document.getElementById('plugin-info').innerHTML = 
                            '<span class="status-error">Failed to load plugins</span>';
                    }
                }
                
                async function submitQuery() {
                    const query = document.getElementById('query-input').value;
                    if (!query.trim()) return;
                    
                    const resultDiv = document.getElementById('query-result');
                    resultDiv.innerHTML = 'Processing...';
                    
                    try {
                        const response = await fetch('/api/query', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ question: query })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            resultDiv.innerHTML = `<div style="margin-top:10px; padding:10px; ` +
                                `background:#f8f9fa; border-radius:4px; white-space:pre-wrap;">` +
                                `${result.result}</div>`;
                        } else {
                            resultDiv.innerHTML = `<div style="color:red;">Error: ${result.error}</div>`;
                        }
                    } catch (error) {
                        resultDiv.innerHTML = `<div style="color:red;">Query failed: ${error.message}</div>`;
                    }
                }
                
                // Load initial data
                loadStatus();
                loadCacheStats();
                loadPlugins();
                
                // Refresh every 30 seconds
                setInterval(() => {
                    loadStatus();
                    loadCacheStats();
                }, 30000);
            </script>
        </body>
        </html>
        """
    
    async def start(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Start the web dashboard server."""
        if not _has_fastapi:
            _log.error("FastAPI not installed, cannot start web dashboard")
            return
        
        try:
            import uvicorn
            
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info",
                access_log=False
            )
            
            server = uvicorn.Server(config)
            
            _log.info(f"Starting web dashboard at http://{host}:{port}")
            await server.serve()
            
        except ImportError:
            _log.error("uvicorn not installed, cannot start web server")
        except Exception as e:
            _log.error(f"Failed to start web dashboard: {e}")
    
    async def stop(self) -> None:
        """Stop the web dashboard server."""
        if self._server_task:
            self._server_task.cancel()
            self._server_task = None
        
        # Close WebSocket connections
        for client in self._websocket_clients:
            try:
                await client.close()
            except Exception:
                pass
        self._websocket_clients.clear()
    
    async def broadcast_event(self, event_type: str, data: Any) -> None:
        """Broadcast event to all connected WebSocket clients."""
        if not self._websocket_clients:
            return
        
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected_clients = []
        for client in self._websocket_clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected_clients.append(client)
        
        # Clean up disconnected clients
        for client in disconnected_clients:
            self._websocket_clients.remove(client)


# Global web dashboard instance
_web_dashboard: WebDashboard | None = None


def get_web_dashboard() -> WebDashboard:
    """Get or create global web dashboard instance."""
    global _web_dashboard
    if _web_dashboard is None:
        _web_dashboard = WebDashboard()
    return _web_dashboard