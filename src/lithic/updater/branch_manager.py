"""Branch manager for update workflow."""

from __future__ import annotations

import subprocess
from pathlib import Path


class BranchManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def create_branch(self, branch_name: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"git checkout timed out after {timeout}s") from exc
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()

    def current_branch(self, timeout: int = 10) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"git rev-parse timed out after {timeout}s") from exc
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()
