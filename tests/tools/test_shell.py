import sys
from pathlib import Path

import pytest

from lithic.tools.shell import CommandError, _is_destructive, run


def test_is_destructive_catches_rm_rf() -> None:
    assert _is_destructive(["rm", "-rf", "/"])


def test_is_destructive_catches_git_reset() -> None:
    assert _is_destructive(["git", "reset", "--hard"])


def test_is_destructive_catches_git_clean() -> None:
    assert _is_destructive(["git", "clean", "-fd"])


def test_is_destructive_allows_safe_git() -> None:
    assert not _is_destructive(["git", "status"])
    assert not _is_destructive(["git", "diff"])


def test_is_destructive_catches_del() -> None:
    assert _is_destructive(["del", "/s", "dir"])


def test_is_destructive_catches_rd() -> None:
    assert _is_destructive(["rd", "/s", "dir"])


def test_is_destructive_catches_remove_item() -> None:
    assert _is_destructive(["remove-item", "dir"])


def test_is_destructive_catches_drop_table() -> None:
    assert _is_destructive(["drop", "table", "users"])


def test_is_destructive_catches_format_volume() -> None:
    assert _is_destructive(["format", "volume", "D:"])


def test_is_destructive_catches_copy_nul() -> None:
    assert _is_destructive(["copy", "nul", "file.txt"])


def test_is_destructive_allows_ls() -> None:
    assert not _is_destructive(["ls", "-la"])


def test_is_destructive_allows_echo() -> None:
    assert not _is_destructive(["echo", "hello"])


def test_is_destructive_catches_python_shutil() -> None:
    assert _is_destructive(["python", "-c", "shutil.rmtree('/')"])


def test_run_with_safe_command(tmp_path: Path) -> None:
    result = run([sys.executable, "-c", "print('hello')"], tmp_path)
    assert "hello" in result


def test_run_with_destructive_raises(tmp_path: Path) -> None:
    with pytest.raises(CommandError, match="refusing destructive"):
        run(["rm", "-rf", "/tmp"], tmp_path)
