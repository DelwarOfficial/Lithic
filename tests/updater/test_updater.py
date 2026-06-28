from pathlib import Path

from lithic_cli.updater.upstream_checker import UpstreamChecker


def test_checker_returns_empty_when_no_lock(tmp_path: Path) -> None:
    checker = UpstreamChecker(tmp_path, tmp_path / "nonexistent.yml")
    assert checker.check() == []


def test_checker_loads_lock_file(tmp_path: Path) -> None:
    lock = tmp_path / "upstream.lock.yml"
    lock.write_text(
        "projects:\n"
        "  graphify:\n"
        "    repo: https://github.com/safishamsi/graphify\n"
        "    branch: v8\n"
        "    commit: abc123\n"
        "    version: 0.8.49\n"
        "    local_path: vendor/graphify\n"
        "    license: MIT\n"
        "    integration: cli_adapter\n",
        encoding="utf-8",
    )
    checker = UpstreamChecker(tmp_path, lock)
    results = checker.check(remote=False)
    assert len(results) >= 1
    assert results[0].name == "graphify"
