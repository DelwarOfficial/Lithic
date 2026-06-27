import pytest

from lithic.policy.response_policy import ResponsePolicy


def test_normal_mode_passthrough() -> None:
    p = ResponsePolicy()
    assert p.shape("hello", mode="normal") == "hello"


def test_high_risk_triggers_safety() -> None:
    p = ResponsePolicy()
    result = p.shape("run: rm -rf /", mode="concise")
    assert "Safety note" in result


def test_commit_mode_formats_type() -> None:
    p = ResponsePolicy()
    result = p.format_commit("fix: resolve auth bug")
    assert result.startswith("fix:")


def test_commit_mode_fallback() -> None:
    p = ResponsePolicy()
    result = p.format_commit("some rough text about changes")
    assert result.startswith("fix:")


def test_review_mode_finds_findings() -> None:
    p = ResponsePolicy()
    result = p.format_review("line1\nline2\n")
    assert result.startswith("-")


def test_concise_drops_filler() -> None:
    p = ResponsePolicy()
    result = p._concise("just a basically simple test here")
    assert "just" not in result
    assert "basically" not in result


def test_unknown_mode_raises() -> None:
    p = ResponsePolicy()
    with pytest.raises(ValueError):
        p.shape("test", mode="unknown")


def test_detect_risk_identifies_destructive() -> None:
    p = ResponsePolicy()
    assert p.detect_risk("rm -rf /") == "high"
    assert p.detect_risk("hello world") == "normal"
    assert p.detect_risk("api token secret") == "medium"


def test_caveman_ultra_removes_articles() -> None:
    p = ResponsePolicy()
    result = p._concise("the quick brown fox ate an apple", ultra=True)
    assert "the" not in result
