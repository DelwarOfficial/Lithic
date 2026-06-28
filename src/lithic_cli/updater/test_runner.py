"""Test runner for update workflow."""

from __future__ import annotations

from pathlib import Path

from lithic_cli.tools.tests import run_pytest


class TestRunner:
    """Run verification commands after planned changes."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def run(self) -> str:
        return run_pytest(self.project_root)
