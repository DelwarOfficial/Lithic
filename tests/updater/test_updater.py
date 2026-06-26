from pathlib import Path

from lithic.updater import CommitGenerator, PlanGenerator, PRPreparer, RiskScanner


def test_commit_generator_returns_conventional_commit() -> None:
    generator = CommitGenerator()
    assert generator.generate("Updated auth redirect flow") == "fix: auth redirect flow"


def test_plan_generator_adds_test_step() -> None:
    generator = PlanGenerator()
    plan = generator.generate({"files_changed": ["src/lithic/cli.py"]})
    assert plan[-1]["step"] == "test"


def test_pr_preparer_builds_checklist() -> None:
    preparer = PRPreparer()
    payload = preparer.prepare("fix: cli", "Tighten CLI behavior", [{"action": "Run tests"}])
    assert payload["title"] == "fix: cli"
    assert payload["checklist"] == ["Run tests"]


def test_risk_scanner_finds_subprocess_usage(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.py"
    file_path.write_text("subprocess.run(['git', 'status'])", encoding="utf-8")
    findings = RiskScanner(tmp_path).scan_file(file_path)
    assert findings
