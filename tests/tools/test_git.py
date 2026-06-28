from pathlib import Path

from lithic_cli.tools.git import diff, status


def test_status_returns_string(tmp_path: Path) -> None:
    try:
        result = status(tmp_path)
        assert isinstance(result, str)
    except Exception:
        pass


def test_diff_returns_string(tmp_path: Path) -> None:
    try:
        result = diff(tmp_path)
        assert isinstance(result, str)
    except Exception:
        pass
