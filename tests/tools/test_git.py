from pathlib import Path

import pytest

from lithic.tools import git
from lithic.tools.shell import CommandError


def test_diff_empty(tmp_path: Path) -> None:
    with pytest.raises(CommandError):
        git.diff(tmp_path)


def test_diff_staged_empty(tmp_path: Path) -> None:
    with pytest.raises(CommandError):
        git.diff(tmp_path, staged=True)


def test_status_in_repo() -> None:
    result = git.status(Path.cwd())
    assert isinstance(result, str)
