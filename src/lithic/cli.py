"""Lithic CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import click
from rich.console import Console

from lithic.config import AgentConfig
from lithic.mcp.server import serve
from lithic.orchestrator import Orchestrator

console = Console()


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Lithic - Carve Knowledge. Compress Context. Deliver Stone-Sharp Precision."""
    ctx.ensure_object(dict)
    config = AgentConfig.from_env(Path.cwd())
    if verbose:
        config = AgentConfig(
            project_root=config.project_root,
            graph_output_dir=config.graph_output_dir,
            provider=config.provider,
            model=config.model,
            response_mode=config.response_mode,
            verbose=True,
        )
    ctx.obj["orchestrator"] = Orchestrator(config)


@main.command()
@click.argument("path", default=".")
@click.pass_context
def index(ctx: click.Context, path: str) -> None:
    """Build or refresh the project graph."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.index(path))


@main.command()
@click.argument("question")
@click.pass_context
def ask(ctx: click.Context, question: str) -> None:
    """Ask an architecture/codebase question."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.ask(question))


@main.command()
@click.argument("concept")
@click.pass_context
def explain(ctx: click.Context, concept: str) -> None:
    """Explain a symbol, module, file, or concept."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.explain(concept))


@main.command("path")
@click.argument("source")
@click.argument("target")
@click.pass_context
def graph_path(ctx: click.Context, source: str, target: str) -> None:
    """Find a relationship path between two graph concepts."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.path_between(source, target))


@main.command()
@click.argument("task")
@click.pass_context
def edit(ctx: click.Context, task: str) -> None:
    """Orient for an edit task without mutating files."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.orient_edit(task))


@main.command()
@click.pass_context
def review(ctx: click.Context) -> None:
    """Review current working-tree diff."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.review())


@main.command()
@click.pass_context
def commit(ctx: click.Context) -> None:
    """Generate a Conventional Commit message."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.commit())


@main.command("compress-file")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_context
def compress_file(ctx: click.Context, file: Path) -> None:
    """Compress a large text file."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    console.print(orch.compress_file(str(file)))


@main.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show graph and compression stats."""
    orch: Orchestrator = ctx.obj["orchestrator"]
    data = cast(dict[str, Any], orch.stats())
    compression = cast(dict[str, Any], data["compression"])
    console.print(f"Graph exists: {data['graph_exists']}")
    console.print(f"History count: {data['history_count']}")
    console.print(f"Compression calls: {compression['calls']}")


@main.command()
def mcp() -> None:
    """Start the MCP server over stdio."""
    serve()
