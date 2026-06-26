"""Shell helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

DESTRUCTIVE = (
    "rm -rf",
    "rm -r",
    "del /s",
    "del /f /s /q",
    "git reset --hard",
    "git clean -fd",
    "drop table",
    "drop database",
    "format volume",
    "remove-item",
    "truncate",
)


def run(command: list[str], cwd: Path, timeout: int = 60) -> str:
    """Run a shell command safely using subprocess list form."""
    joined = " ".join(command).lower()
    if any(token in joined for token in DESTRUCTIVE):
        raise ValueError(f"refusing destructive command without confirmation: {' '.join(command)}")
    try:
        result = subprocess.run(
            command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"command timed out after {timeout}s: {' '.join(command)}") from exc
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    if result.returncode != 0:
        raise RuntimeError(output or "command failed")
    return output
