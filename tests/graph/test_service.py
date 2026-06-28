from pathlib import Path

from lithic_cli.graph.service import GraphService


def test_ttl_cache_returns_cached_query(monkeypatch, tmp_path: Path) -> None:
    gs = GraphService(tmp_path, tmp_path / "graphify-out")
    call_count: int = 0

    def fake_query(q: str) -> str:
        nonlocal call_count
        call_count += 1
        return f"answer:{q}"

    monkeypatch.setattr(gs._adapter, "query", fake_query)
    first = gs.query("how auth?")
    second = gs.query("how auth?")
    assert first == "answer:how auth?"
    assert second == first
    assert call_count == 1


def test_ttl_cache_misses_on_different_keys(monkeypatch, tmp_path: Path) -> None:
    gs = GraphService(tmp_path, tmp_path / "graphify-out")
    calls: list[str] = []

    def fake_query(q: str) -> str:
        calls.append(q)
        return f"answer:{q}"

    monkeypatch.setattr(gs._adapter, "query", fake_query)
    gs.query("q1")
    gs.query("q2")
    gs.query("q1")
    assert calls == ["q1", "q2"]


def test_clear_cache_resets(monkeypatch, tmp_path: Path) -> None:
    gs = GraphService(tmp_path, tmp_path / "graphify-out")
    call_count: int = 0

    def fake_query(q: str) -> str:
        nonlocal call_count
        call_count += 1
        return f"answer:{q}"

    monkeypatch.setattr(gs._adapter, "query", fake_query)
    gs.query("q")
    gs.query("q")
    assert call_count == 1
    gs.clear_cache()
    gs.query("q")
    assert call_count == 2


def test_ttl_cache_for_explain(monkeypatch, tmp_path: Path) -> None:
    gs = GraphService(tmp_path, tmp_path / "graphify-out")
    call_count: int = 0

    def fake_explain(c: str) -> str:
        nonlocal call_count
        call_count += 1
        return f"explain:{c}"

    monkeypatch.setattr(gs._adapter, "explain", fake_explain)
    assert gs.explain("Foo") == "explain:Foo"
    assert gs.explain("Foo") == "explain:Foo"
    assert call_count == 1


def test_ttl_cache_for_path(monkeypatch, tmp_path: Path) -> None:
    gs = GraphService(tmp_path, tmp_path / "graphify-out")
    call_count: int = 0

    def fake_path(s: str, t: str) -> str:
        nonlocal call_count
        call_count += 1
        return f"path:{s}->{t}"

    monkeypatch.setattr(gs._adapter, "path_between", fake_path)
    assert gs.path_between("A", "B") == "path:A->B"
    assert gs.path_between("A", "B") == "path:A->B"
    assert call_count == 1
    assert gs.path_between("A", "C") == "path:A->C"
    assert call_count == 2
