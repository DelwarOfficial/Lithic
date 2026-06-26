"""PR preparation helpers for updater workflow."""

from __future__ import annotations

from typing import Any


class PRPreparer:
    """Prepare a lightweight pull request payload."""

    def prepare(self, title: str, summary: str, plan: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "title": title,
            "summary": summary.strip(),
            "checklist": [item.get("action", "") for item in plan if item.get("action")],
        }
