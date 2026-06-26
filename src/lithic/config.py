"""Configuration models and environment loading for Lithic."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


@dataclass(frozen=True)
class AgentConfig:
    """Runtime configuration for Lithic."""

    project_root: Path
    graph_output_dir: Path
    provider: str = "local"
    model: str = "gpt-4.1-mini"
    response_mode: str = "concise"
    verbose: bool = False

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> AgentConfig:
        """Load config from process env and optional local `.env`."""
        root = (project_root or Path.cwd()).resolve()
        load_dotenv(root / ".env", override=False)
        graph_dir_raw = _env(
            "LITHIC_GRAPH_DIR",
            "UDA_GRAPH_DIR",
            default=str(root / "graphify-out"),
        )
        return cls(
            project_root=root,
            graph_output_dir=Path(graph_dir_raw or root / "graphify-out").resolve(),
            provider=_env("LITHIC_PROVIDER", "UDA_PROVIDER", default="local") or "local",
            model=_env("LITHIC_MODEL", "UDA_MODEL", default="gpt-4.1-mini") or "gpt-4.1-mini",
            response_mode=_env("LITHIC_RESPONSE_MODE", "UDA_RESPONSE_MODE", default="concise")
            or "concise",
            verbose=(_env("LITHIC_VERBOSE", default="0") or "0").lower()
            in {"1", "true", "yes", "on"},
        )
