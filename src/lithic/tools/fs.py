"""Filesystem helpers."""

from __future__ import annotations

from pathlib import Path


def resolve_path_within_root(root: Path, candidate: Path | str) -> Path:
    """Resolve a path and ensure it stays inside the given root."""
    candidate_path = Path(candidate)
    if candidate_path.is_absolute():
        path = candidate_path.resolve()
    else:
        path = (root / candidate_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"path must stay inside project root: {path}") from exc
    return path


def read_text(path: Path, max_chars: int = 12000) -> str:
    """Read text with truncation for large files."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text if len(text) <= max_chars else text[:max_chars] + "\n... [truncated] ..."
