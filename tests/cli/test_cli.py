from types import SimpleNamespace

from click.testing import CliRunner

import lithic.cli as lithic_cli
from lithic.cli import main


def test_ask_command(monkeypatch) -> None:
    monkeypatch.setattr(lithic_cli.Orchestrator, "ask", lambda self, question: "answer")
    result = CliRunner().invoke(main, ["ask", "how auth works?"])
    assert result.exit_code == 0
    assert "answer" in result.output


def test_index_command(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        lithic_cli.Orchestrator,
        "index",
        lambda self, path: f"Graph built at {tmp_path / 'graph.json'}",
    )
    result = CliRunner().invoke(main, ["index", "."])
    assert result.exit_code == 0
    assert "Graph built at" in result.output


def test_stats_command(monkeypatch) -> None:
    monkeypatch.setattr(
        lithic_cli.Orchestrator,
        "stats",
        lambda self: {"graph_exists": True, "history_count": 2, "compression": {"calls": 3}},
    )
    result = CliRunner().invoke(main, ["stats"])
    assert result.exit_code == 0
    assert "Compression calls: 3" in result.output


def test_upstream_status_command(monkeypatch) -> None:
    class FakeChecker:
        def __init__(self, project_root):
            self.project_root = project_root

        def check(self, *, remote=True):
            assert remote is False
            return [
                SimpleNamespace(
                    name="graphify",
                    status="up-to-date",
                    local_commit="abc123456789",
                    remote_commit="",
                    error="",
                )
            ]

    monkeypatch.setattr(lithic_cli, "UpstreamChecker", FakeChecker)
    result = CliRunner().invoke(main, ["upstream-status", "--local-only"])
    assert result.exit_code == 0
    assert "graphify: up-to-date abc123456789" in result.output


def test_lithic_package_entrypoint(monkeypatch) -> None:
    monkeypatch.setattr(lithic_cli.Orchestrator, "ask", lambda self, question: "answer")
    result = CliRunner().invoke(lithic_cli.main, ["ask", "how auth works?"])
    assert result.exit_code == 0
    assert "answer" in result.output
