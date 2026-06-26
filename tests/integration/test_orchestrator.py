from pathlib import Path

from lithic.config import AgentConfig
from lithic.orchestrator import Orchestrator


def _orch(tmp_path: Path) -> Orchestrator:
    return Orchestrator(
        AgentConfig(project_root=tmp_path, graph_output_dir=tmp_path / "graphify-out")
    )


def test_graph_first_behavior(monkeypatch, tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    monkeypatch.setattr(orch.graph, "query", lambda question: "graph answer")
    assert orch.ask("how auth works") == "graph answer"
    assert orch.events == ["graph.query"]


def test_explain_uses_graph(monkeypatch, tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    monkeypatch.setattr(orch.graph, "explain", lambda concept: f"about {concept}")
    assert orch.explain("UserService") == "about UserService"
    assert orch.events == ["graph.explain"]


def test_stats_shape(tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    stats = orch.stats()
    assert "graph" in stats
    assert "compression" in stats


def test_commit_uses_diff(monkeypatch, tmp_path: Path) -> None:
    orch = _orch(tmp_path)
    monkeypatch.setattr(
        "lithic.orchestrator.git.diff",
        lambda root, staged=False: "bug in auth redirect",
    )
    out = orch.commit()
    assert out.startswith("fix:")
