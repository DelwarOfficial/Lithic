"""Git helpers."""

from __future__ import annotations

from pathlib import Path

from lithic_cli.tools.shell import run


def status(root: Path) -> str:
    """Return `git status --short` output."""
    return run(["git", "status", "--short"], root)


def diff(root: Path, staged: bool = False) -> str:
    """Return staged or working-tree diff output."""
    return run(["git", "diff", "--staged"] if staged else ["git", "diff"], root)
