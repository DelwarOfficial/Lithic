from lithic.policy.response_policy import ResponsePolicy


def test_preserves_code_blocks() -> None:
    policy = ResponsePolicy()
    code = "```python\nprint('exact')\n```"
    out = policy.shape(f"Sure, basically use this:\n{code}", mode="caveman_full")
    assert code in out


def test_risky_switches_to_safety_clear() -> None:
    policy = ResponsePolicy()
    out = policy.shape("run `git reset --hard`", mode="caveman_ultra")
    assert out.startswith("Safety note:")
    assert "`git reset --hard`" in out


def test_commit_message() -> None:
    policy = ResponsePolicy()
    out = policy.shape("Updated login redirect handling", mode="commit")
    assert out == "fix: login redirect handling"


def test_review_output() -> None:
    policy = ResponsePolicy()
    out = policy.shape("bug in auth redirect", mode="review")
    assert "medium" in out
    assert "bug in auth redirect" in out


def test_commit_message_normalizes_subject() -> None:
    policy = ResponsePolicy()
    out = policy.format_commit("- Added provider configuration loading.")
    assert out == "fix: provider configuration loading"
