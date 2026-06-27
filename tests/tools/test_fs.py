from pathlib import Path

import pytest

from lithic.tools.fs import read_text, resolve_path_within_root


def test_resolve_within_root(tmp_path: Path) -> None:
    child = tmp_path / "sub" / "file.txt"
    child.parent.mkdir(parents=True)
    child.write_text("test", encoding="utf-8")
    result = resolve_path_within_root(tmp_path, child)
    assert result == child.resolve()


def test_resolve_outside_root_raises(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    with pytest.raises(ValueError, match="must stay inside"):
        resolve_path_within_root(tmp_path, outside)


def test_resolve_absolute_path(tmp_path: Path) -> None:
    child = tmp_path / "file.txt"
    child.write_text("test", encoding="utf-8")
    result = resolve_path_within_root(tmp_path, str(child))
    assert result == child.resolve()


def test_read_text_short(tmp_path: Path) -> None:
    f = tmp_path / "short.txt"
    f.write_text("hello", encoding="utf-8")
    assert read_text(f, max_chars=100) == "hello"


def test_read_text_truncated(tmp_path: Path) -> None:
    f = tmp_path / "long.txt"
    f.write_text("a" * 1000, encoding="utf-8")
    result = read_text(f, max_chars=100)
    assert len(result) <= 120
    assert "... [truncated] ..." in result


def test_resolve_symlink_inside_root(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("data", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    result = resolve_path_within_root(tmp_path, link)
    assert result == target.resolve()


def test_resolve_dot_dot_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must stay inside"):
        resolve_path_within_root(tmp_path, "../outside.txt")
