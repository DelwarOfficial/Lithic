"""Patch applier for update workflow."""

from __future__ import annotations

import subprocess
from pathlib import Path


class PatchApplier:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def apply_patch(self, patch_text: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                ["git", "apply"],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                check=False,
                input=patch_text,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"git apply timed out after {timeout}s") from exc
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()
