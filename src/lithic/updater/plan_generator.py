"""Plan generator for update workflow."""

from __future__ import annotations

from typing import Any


class PlanGenerator:
    def generate(self, analysis: dict[str, Any]) -> list[dict[str, str]]:
        files = analysis.get("files_changed")
        if not isinstance(files, list):
            files = []
        if not files:
            return [{"step": "noop", "action": "No changes detected"}]
        plan = []
        for f in files:
            if isinstance(f, str):
                plan.append({
                    "step": f"review {f}",
                    "action": f"Review changes in {f}",
                })
        plan.append({"step": "test", "action": "Run tests to verify"})
        return plan
