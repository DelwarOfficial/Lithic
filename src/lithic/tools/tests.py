"""Test runner helpers."""

from __future__ import annotations

from pathlib import Path

from lithic.tools.shell import run


def run_pytest(root: Path) -> str:
    """Run the project pytest suite."""
    return run(["uv", "run", "pytest"], root)
