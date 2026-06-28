"""Commit message generator for updater workflow."""

from __future__ import annotations

from lithic_cli.policy.response_policy import ResponsePolicy


class CommitGenerator:
    """Generate Conventional Commit subjects from change summaries."""

    def __init__(self) -> None:
        self.policy = ResponsePolicy()

    def generate(self, summary: str) -> str:
        return self.policy.format_commit(summary)
