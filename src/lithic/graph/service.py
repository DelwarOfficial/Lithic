"""Graph service wrapping GraphifyAdapter."""

from __future__ import annotations

from pathlib import Path

from lithic.graph.graphify_adapter import GraphifyAdapter


class GraphService:
    """Wraps graph operations behind a stable service interface."""

    def __init__(self, project_root: Path, graph_output_dir: Path | None = None) -> None:
        self._adapter = GraphifyAdapter(project_root, graph_output_dir)

    @property
    def graph_path(self) -> Path:
        return self._adapter.graph_path

    def query(self, question: str) -> str:
        return self._adapter.query(question)

    def explain(self, concept: str) -> str:
        return self._adapter.explain(concept)

    def path_between(self, source: str, target: str) -> str:
        return self._adapter.path_between(source, target)

    def build_graph(self, target_path: str = ".") -> Path:
        return self._adapter.build_graph(target_path)

    def graph_exists(self) -> bool:
        return self._adapter.graph_exists()

    def stats(self) -> dict[str, int | str]:
        return self._adapter.stats()
