"""Microservices architecture for distributed Lithic deployment."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

_log = logging.getLogger("lithic_cli.microservices")


class ServiceType(Enum):
    """Service type definitions."""
    GRAPH = "graph"
    COMPRESSION = "compression" 
    LLM = "llm"
    CACHE = "cache"
    GATEWAY = "gateway"
    MONITOR = "monitor"


@dataclass
class ServiceConfig:
    """Service configuration."""
    name: str
    service_type: ServiceType
    host: str = "localhost"
    port: int = 8000
    health_port: int = 8080
    metrics_port: int = 9090
    replicas: int = 1
    max_memory_mb: int = 512
    max_cpu_cores: float = 1.0
    env_vars: dict[str, str] = None
    
    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}


@dataclass  
class ServiceInstance:
    """Running service instance."""
    config: ServiceConfig
    instance_id: str
    pid: int | None = None
    status: str = "starting"
    started_at: datetime | None = None
    last_health_check: datetime | None = None
    health_status: str = "unknown"
    metrics: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


class ServiceRegistry:
    """Service discovery and registration."""
    
    def __init__(self):
        self._services: dict[str, ServiceInstance] = {}
        self._type_index: dict[ServiceType, list[str]] = {}
    
    def register(self, instance: ServiceInstance) -> bool:
        """Register service instance."""
        service_name = f"{instance.config.name}-{instance.instance_id}"
        self._services[service_name] = instance
        
        # Update type index
        service_type = instance.config.service_type
        if service_type not in self._type_index:
            self._type_index[service_type] = []
        self._type_index[service_type].append(service_name)
        
        _log.info(f"Registered service {service_name}")
        return True
    
    def unregister(self, service_name: str) -> bool:
        """Unregister service instance."""
        if service_name not in self._services:
            return False
        
        instance = self._services[service_name]
        service_type = instance.config.service_type
        
        # Remove from indexes
        del self._services[service_name]
        if service_type in self._type_index:
            self._type_index[service_type] = [
                name for name in self._type_index[service_type] 
                if name != service_name
            ]
        
        _log.info(f"Unregistered service {service_name}")
        return True
    
    def find_services(self, service_type: ServiceType) -> list[ServiceInstance]:
        """Find services by type."""
        service_names = self._type_index.get(service_type, [])
        return [self._services[name] for name in service_names if name in self._services]
    
    def get_service(self, service_name: str) -> ServiceInstance | None:
        """Get specific service instance."""
        return self._services.get(service_name)
    
    def list_all(self) -> list[ServiceInstance]:
        """List all registered services."""
        return list(self._services.values())
    
    def health_summary(self) -> dict[str, Any]:
        """Get health summary of all services."""
        total = len(self._services)
        healthy = sum(1 for s in self._services.values() if s.health_status == "healthy")
        
        by_type = {}
        for service_type in ServiceType:
            instances = self.find_services(service_type)
            by_type[service_type.value] = {
                "total": len(instances),
                "healthy": sum(1 for s in instances if s.health_status == "healthy")
            }
        
        return {
            "total_services": total,
            "healthy_services": healthy,
            "health_rate": healthy / total if total > 0 else 0,
            "by_type": by_type
        }


class ServiceManager:
    """Manages service lifecycle and orchestration."""
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self._running_processes: dict[str, asyncio.subprocess.Process] = {}
        self._health_tasks: dict[str, asyncio.Task] = {}
    
    async def start_service(self, config: ServiceConfig, instance_id: str = "1") -> bool:
        """Start a service instance."""
        service_name = f"{config.name}-{instance_id}"
        
        if service_name in self._running_processes:
            _log.warning(f"Service {service_name} already running")
            return False
        
        try:
            # Create service instance record
            instance = ServiceInstance(
                config=config,
                instance_id=instance_id,
                started_at=datetime.now()
            )
            
            # Start the process
            cmd = self._build_service_command(config, instance_id)
            env = os.environ.copy()
            env.update(config.env_vars)
            env.update({
                "LITHIC_SERVICE_NAME": config.name,
                "LITHIC_INSTANCE_ID": instance_id,
                "LITHIC_SERVICE_TYPE": config.service_type.value,
                "LITHIC_PORT": str(config.port),
                "LITHIC_HEALTH_PORT": str(config.health_port)
            })
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            instance.pid = process.pid
            instance.status = "running"
            
            # Register service
            self.registry.register(instance)
            self._running_processes[service_name] = process
            
            # Start health monitoring
            health_task = asyncio.create_task(
                self._monitor_service_health(service_name)
            )
            self._health_tasks[service_name] = health_task
            
            _log.info(f"Started service {service_name} with PID {process.pid}")
            return True
            
        except Exception as e:
            _log.error(f"Failed to start service {service_name}: {e}")
            return False
    
    def _build_service_command(self, config: ServiceConfig, instance_id: str) -> list[str]:
        """Build command to start service."""
        if config.service_type == ServiceType.GRAPH:
            return ["python", "-m", "lithic_cli.microservices.graph_service"]
        elif config.service_type == ServiceType.COMPRESSION:
            return ["python", "-m", "lithic_cli.microservices.compression_service"]
        elif config.service_type == ServiceType.LLM:
            return ["python", "-m", "lithic_cli.microservices.llm_service"]
        elif config.service_type == ServiceType.CACHE:
            return ["python", "-m", "lithic_cli.microservices.cache_service"]
        elif config.service_type == ServiceType.GATEWAY:
            return ["python", "-m", "lithic_cli.microservices.gateway_service"]
        elif config.service_type == ServiceType.MONITOR:
            return ["python", "-m", "lithic_cli.microservices.monitor_service"]
        else:
            raise ValueError(f"Unknown service type: {config.service_type}")
    
    async def stop_service(self, service_name: str) -> bool:
        """Stop a service instance."""
        if service_name not in self._running_processes:
            return False
        
        try:
            # Cancel health monitoring
            if service_name in self._health_tasks:
                self._health_tasks[service_name].cancel()
                del self._health_tasks[service_name]
            
            # Stop process
            process = self._running_processes[service_name]
            process.terminate()
            
            try:
                await asyncio.wait_for(process.wait(), timeout=10)
            except TimeoutError:
                process.kill()
                await process.wait()
            
            # Cleanup
            del self._running_processes[service_name]
            self.registry.unregister(service_name)
            
            _log.info(f"Stopped service {service_name}")
            return True
            
        except Exception as e:
            _log.error(f"Failed to stop service {service_name}: {e}")
            return False
    
    async def stop_all_services(self) -> None:
        """Stop all running services."""
        service_names = list(self._running_processes.keys())
        for service_name in service_names:
            await self.stop_service(service_name)
    
    async def _monitor_service_health(self, service_name: str) -> None:
        """Monitor service health continuously."""
        while service_name in self._running_processes:
            try:
                instance = self.registry.get_service(service_name)
                if not instance:
                    break
                
                # Simple health check - process still running
                process = self._running_processes[service_name]
                if process.returncode is not None:
                    instance.status = "crashed"
                    instance.health_status = "unhealthy"
                else:
                    instance.status = "running"
                    instance.health_status = "healthy"
                
                instance.last_health_check = datetime.now()
                
                # TODO: Add HTTP health check to service health endpoints
                
                await asyncio.sleep(30)  # Health check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                _log.error(f"Health monitoring error for {service_name}: {e}")
                await asyncio.sleep(30)
    
    async def scale_service(self, service_type: ServiceType, target_replicas: int) -> bool:
        """Scale service to target number of replicas."""
        current_instances = self.registry.find_services(service_type)
        current_replicas = len(current_instances)
        
        if target_replicas == current_replicas:
            return True
        
        if target_replicas > current_replicas:
            # Scale up
            if not current_instances:
                _log.error(f"No existing instances of {service_type} to scale from")
                return False
            
            base_config = current_instances[0].config
            for i in range(current_replicas + 1, target_replicas + 1):
                # Create new config with adjusted port
                new_config = ServiceConfig(
                    name=base_config.name,
                    service_type=base_config.service_type,
                    host=base_config.host,
                    port=base_config.port + i - 1,
                    health_port=base_config.health_port + i - 1,
                    replicas=1,
                    max_memory_mb=base_config.max_memory_mb,
                    max_cpu_cores=base_config.max_cpu_cores,
                    env_vars=base_config.env_vars.copy()
                )
                
                await self.start_service(new_config, str(i))
        
        else:
            # Scale down
            instances_to_stop = current_instances[target_replicas:]
            for instance in instances_to_stop:
                service_name = f"{instance.config.name}-{instance.instance_id}"
                await self.stop_service(service_name)
        
        _log.info(f"Scaled {service_type} from {current_replicas} to {target_replicas} replicas")
        return True
    
    def get_service_stats(self) -> dict[str, Any]:
        """Get comprehensive service statistics."""
        return {
            "registry": self.registry.health_summary(),
            "running_processes": len(self._running_processes),
            "health_monitors": len(self._health_tasks)
        }


class ServiceClient:
    """Client for communicating with microservices."""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
    
    async def call_service(self, service_type: ServiceType, method: str, 
                          data: dict[str, Any] = None) -> dict[str, Any]:
        """Call a service method with load balancing."""
        instances = self.registry.find_services(service_type)
        healthy_instances = [
            i for i in instances if i.health_status == "healthy"
        ]
        
        if not healthy_instances:
            raise RuntimeError(f"No healthy {service_type} instances available")
        
        # Simple round-robin load balancing
        instance = healthy_instances[0]  # Simplified
        
        # TODO: Implement actual HTTP client call
        _log.info(f"Calling {method} on {service_type} service at {instance.config.host}:{instance.config.port}")
        
        # Mock response for now
        return {"status": "success", "data": data}


# Global service manager
_service_manager: ServiceManager | None = None


def get_service_manager() -> ServiceManager:
    """Get or create global service manager."""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager


# Default service configurations
DEFAULT_SERVICES = [
    ServiceConfig(
        name="lithic-graph",
        service_type=ServiceType.GRAPH,
        port=8001,
        health_port=8081,
        max_memory_mb=1024
    ),
    ServiceConfig(
        name="lithic-compression", 
        service_type=ServiceType.COMPRESSION,
        port=8002,
        health_port=8082,
        max_memory_mb=512
    ),
    ServiceConfig(
        name="lithic-cache",
        service_type=ServiceType.CACHE,
        port=8003,
        health_port=8083,
        max_memory_mb=2048
    ),
    ServiceConfig(
        name="lithic-gateway",
        service_type=ServiceType.GATEWAY,
        port=8000,
        health_port=8080,
        max_memory_mb=256
    )
]