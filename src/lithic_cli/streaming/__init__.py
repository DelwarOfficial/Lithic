"""Async streaming processing for real-time operations."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio import Queue
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

_log = logging.getLogger("lithic_cli.streaming")


class EventType(Enum):
    """Stream event types."""
    DATA = "data"
    ERROR = "error"
    COMPLETE = "complete"
    METADATA = "metadata"


@dataclass
class StreamEvent:
    """Stream event with type, data, and metadata."""
    type: EventType
    data: Any
    timestamp: datetime
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StreamProcessor(ABC):
    """Abstract stream processor interface."""
    
    @abstractmethod
    async def process(self, event: StreamEvent) -> AsyncGenerator[StreamEvent, None]:
        """Process stream event and yield results."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize processor resources."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup processor resources."""
        pass


class AsyncStreamPipeline:
    """Composable async stream processing pipeline."""
    
    def __init__(self, buffer_size: int = 1000):
        self.processors: list[StreamProcessor] = []
        self.buffer_size = buffer_size
        self._running = False
        self._input_queue: Queue = None
        self._tasks: list[asyncio.Task] = []
    
    def add_processor(self, processor: StreamProcessor) -> AsyncStreamPipeline:
        """Add processor to pipeline."""
        self.processors.append(processor)
        return self
    
    async def start(self) -> None:
        """Start pipeline processing."""
        if self._running:
            return
        
        self._input_queue = Queue(maxsize=self.buffer_size)
        self._running = True
        
        # Initialize all processors
        for processor in self.processors:
            await processor.initialize()
        
        _log.info(f"Started stream pipeline with {len(self.processors)} processors")
    
    async def stop(self) -> None:
        """Stop pipeline and cleanup."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Cleanup processors  
        for processor in self.processors:
            await processor.cleanup()
        
        self._tasks.clear()
        _log.info("Stopped stream pipeline")
    
    async def push(self, data: Any, metadata: dict[str, Any] = None) -> None:
        """Push data into pipeline."""
        if not self._running:
            raise RuntimeError("Pipeline not started")
        
        event = StreamEvent(
            type=EventType.DATA,
            data=data,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        await self._input_queue.put(event)
    
    async def process_stream(self) -> AsyncGenerator[StreamEvent, None]:
        """Process events through pipeline."""
        if not self._running:
            raise RuntimeError("Pipeline not started")
        
        while self._running:
            try:
                # Get event from input queue
                event = await asyncio.wait_for(self._input_queue.get(), timeout=1.0)
                
                # Process through pipeline
                current_events = [event]
                
                for processor in self.processors:
                    next_events = []
                    for evt in current_events:
                        async for result_event in processor.process(evt):
                            next_events.append(result_event)
                    current_events = next_events
                
                # Yield final events
                for final_event in current_events:
                    yield final_event
                    
            except TimeoutError:
                # No events to process, continue
                continue
            except Exception as e:
                _log.error(f"Pipeline processing error: {e}")
                error_event = StreamEvent(
                    type=EventType.ERROR,
                    data=str(e),
                    timestamp=datetime.now(),
                    metadata={"error_type": type(e).__name__}
                )
                yield error_event


class FileWatchProcessor(StreamProcessor):
    """Processor for file system events."""
    
    def __init__(self, watch_paths: list[str], patterns: list[str] = None):
        self.watch_paths = watch_paths
        self.patterns = patterns or ["**/*.py", "**/*.md", "**/*.json"]
        self._watcher = None
    
    async def initialize(self) -> None:
        """Setup file watcher."""
        try:
            from watchfiles import awatch
            self._awatch = awatch
            _log.info(f"Initialized file watcher for {len(self.watch_paths)} paths")
        except ImportError:
            _log.warning("watchfiles not installed, file watching disabled")
            self._awatch = None
    
    async def process(self, event: StreamEvent) -> AsyncGenerator[StreamEvent, None]:
        """Process file watch events."""
        if self._awatch is None:
            return
        
        if event.type == EventType.DATA and event.data.get("type") == "file_watch":
            try:
                async for changes in self._awatch(*self.watch_paths):
                    for change_type, path in changes:
                        file_event = StreamEvent(
                            type=EventType.DATA,
                            data={
                                "type": "file_change",
                                "change_type": change_type.name,
                                "path": str(path)
                            },
                            timestamp=datetime.now(),
                            metadata={"source": "file_watcher"}
                        )
                        yield file_event
            except Exception as e:
                _log.error(f"File watcher error: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup watcher resources."""
        pass


class GraphUpdateProcessor(StreamProcessor):
    """Processor for graph update events."""
    
    def __init__(self, graph_service=None):
        self.graph_service = graph_service
        self._update_queue = asyncio.Queue()
    
    async def initialize(self) -> None:
        """Initialize graph processor."""
        _log.info("Initialized graph update processor")
    
    async def process(self, event: StreamEvent) -> AsyncGenerator[StreamEvent, None]:
        """Process graph update events."""
        if event.type == EventType.DATA:
            data = event.data
            
            # Handle file changes
            if data.get("type") == "file_change" and self.graph_service:
                file_path = data.get("path")
                change_type = data.get("change_type")
                
                try:
                    # Trigger incremental graph update
                    if change_type in ["added", "modified"]:
                        # Add to update queue for batch processing
                        await self._update_queue.put(file_path)
                    
                    update_event = StreamEvent(
                        type=EventType.DATA,
                        data={
                            "type": "graph_update_queued",
                            "file": file_path,
                            "change": change_type
                        },
                        timestamp=datetime.now(),
                        metadata={"processor": "graph_update"}
                    )
                    yield update_event
                    
                except Exception as e:
                    _log.error(f"Graph update error: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup graph processor."""
        pass


class CompressionProcessor(StreamProcessor):
    """Processor for content compression."""
    
    def __init__(self, compression_provider=None, threshold: int = 1000):
        self.compression_provider = compression_provider
        self.threshold = threshold
    
    async def initialize(self) -> None:
        """Initialize compression processor."""
        _log.info("Initialized compression processor")
    
    async def process(self, event: StreamEvent) -> AsyncGenerator[StreamEvent, None]:
        """Process compression events."""
        if event.type == EventType.DATA and self.compression_provider:
            data = event.data
            
            # Compress large text content
            if isinstance(data.get("content"), str):
                content = data["content"]
                if len(content) > self.threshold:
                    try:
                        result = self.compression_provider.compress_text(content)
                        if result.success:
                            compressed_event = StreamEvent(
                                type=EventType.DATA,
                                data={
                                    **data,
                                    "content": result.data,
                                    "original_size": len(content),
                                    "compressed_size": len(result.data)
                                },
                                timestamp=datetime.now(),
                                metadata={**event.metadata, "compressed": True}
                            )
                            yield compressed_event
                            return
                    except Exception as e:
                        _log.error(f"Compression error: {e}")
            
        # Pass through unchanged
        yield event
    
    async def cleanup(self) -> None:
        """Cleanup compression processor."""
        pass


class MetricsProcessor(StreamProcessor):
    """Processor for metrics collection and monitoring."""
    
    def __init__(self):
        self.event_count = 0
        self.error_count = 0
        self.processing_times = []
        self._start_time = None
    
    async def initialize(self) -> None:
        """Initialize metrics processor."""
        self._start_time = datetime.now()
        _log.info("Initialized metrics processor")
    
    async def process(self, event: StreamEvent) -> AsyncGenerator[StreamEvent, None]:
        """Process metrics events."""
        start_time = datetime.now()
        
        self.event_count += 1
        if event.type == EventType.ERROR:
            self.error_count += 1
        
        # Emit metrics periodically
        if self.event_count % 100 == 0:
            metrics_event = StreamEvent(
                type=EventType.METADATA,
                data={
                    "type": "metrics",
                    "event_count": self.event_count,
                    "error_count": self.error_count,
                    "error_rate": self.error_count / self.event_count,
                    "uptime_seconds": (datetime.now() - self._start_time).total_seconds()
                },
                timestamp=datetime.now(),
                metadata={"source": "metrics_processor"}
            )
            yield metrics_event
        
        # Pass through original event
        yield event
        
        # Track processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        self.processing_times.append(processing_time)
        
        # Keep only recent processing times
        if len(self.processing_times) > 1000:
            self.processing_times = self.processing_times[-500:]
    
    async def cleanup(self) -> None:
        """Cleanup metrics processor."""
        pass


async def create_default_pipeline() -> AsyncStreamPipeline:
    """Create default streaming pipeline with common processors."""
    pipeline = AsyncStreamPipeline(buffer_size=2000)
    
    # Add default processors
    pipeline.add_processor(FileWatchProcessor(["."], ["**/*.py", "**/*.md", "**/*.json"]))
    pipeline.add_processor(GraphUpdateProcessor())
    pipeline.add_processor(CompressionProcessor(threshold=2000))
    pipeline.add_processor(MetricsProcessor())
    
    return pipeline


# Global streaming instance
_global_pipeline: AsyncStreamPipeline | None = None


async def get_stream_pipeline() -> AsyncStreamPipeline:
    """Get or create global streaming pipeline."""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = await create_default_pipeline()
        await _global_pipeline.start()
    return _global_pipeline