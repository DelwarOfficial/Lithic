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


def test_lithic_package_entrypoint(monkeypatch) -> None:
    monkeypatch.setattr(lithic_cli.Orchestrator, "ask", lambda self, question: "answer")
    result = CliRunner().invoke(lithic_cli.main, ["ask", "how auth works?"])
    assert result.exit_code == 0
    assert "answer" in result.output
