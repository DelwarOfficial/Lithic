"""Lithic public package API."""

from importlib.metadata import PackageNotFoundError, version

from lithic_cli.cli import main
from lithic_cli.config import AgentConfig
from lithic_cli.orchestrator import Orchestrator

try:
    __version__ = version("lithic-cli")
except PackageNotFoundError:
    __version__ = "0.2.0"

__all__ = ["AgentConfig", "Orchestrator", "main", "__version__"]
