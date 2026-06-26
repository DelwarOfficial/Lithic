"""MCP server for Lithic."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic import BaseModel

from lithic.compression.headroom_adapter import HeadroomAdapter
from lithic.orchestrator import Orchestrator


class QueryInput(BaseModel):
    """Graph query input schema."""

    question: str


class ExplainInput(BaseModel):
    """Graph explain input schema."""

    concept: str


class PathInput(BaseModel):
    """Graph path input schema."""

    source: str
    target: str


class CompressInput(BaseModel):
    """Compression input schema."""

    text: str


def _tool_result(text: str) -> list[Any]:
    from mcp.types import TextContent

    return [TextContent(type="text", text=text)]


def build_server() -> Any:
    """Build an MCP stdio server for Lithic tools."""
    try:
        from mcp.server import Server
        from mcp.types import Tool
    except ImportError as exc:
        raise RuntimeError("mcp package is not installed. Install with `uv add mcp`.") from exc

    server = Server("lithic")
    orch = Orchestrator()
    compressor = HeadroomAdapter()

    @server.list_tools()
    async def list_tools() -> list[Any]:
        return [
            Tool(
                name="lithic_graph_query",
                description="Query the project graph",
                inputSchema=QueryInput.model_json_schema(),
            ),
            Tool(
                name="lithic_graph_explain",
                description="Explain a graph concept",
                inputSchema=ExplainInput.model_json_schema(),
            ),
            Tool(
                name="lithic_graph_path",
                description="Find a path between graph concepts",
                inputSchema=PathInput.model_json_schema(),
            ),
            Tool(
                name="lithic_compress",
                description="Compress text safely",
                inputSchema=CompressInput.model_json_schema(),
            ),
            Tool(name="lithic_review", description="Review current diff", inputSchema={}),
            Tool(name="lithic_commit", description="Write commit message", inputSchema={}),
            Tool(name="lithic_stats", description="Return stats", inputSchema={}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> list[Any]:
        args = arguments or {}
        try:
            if name == "lithic_graph_query":
                return _tool_result(orch.ask(QueryInput(**args).question))
            if name == "lithic_graph_explain":
                return _tool_result(orch.explain(ExplainInput(**args).concept))
            if name == "lithic_graph_path":
                data = PathInput(**args)
                return _tool_result(orch.path_between(data.source, data.target))
            if name == "lithic_compress":
                return _tool_result(compressor.compress_text(CompressInput(**args).text))
            if name == "lithic_review":
                return _tool_result(orch.review())
            if name == "lithic_commit":
                return _tool_result(orch.commit())
            if name == "lithic_stats":
                return _tool_result(json.dumps(orch.stats(), indent=2))
            return _tool_result(f"unknown tool: {name}")
        except Exception as exc:
            return _tool_result(f"error: {exc}")

    return server


async def _serve_async() -> None:
    from mcp.server.stdio import stdio_server

    server = build_server()
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


def serve() -> None:
    """Serve Lithic MCP tools over stdio."""
    asyncio.run(_serve_async())
