from lithic.tools.audit import _summarize, tool_call


def test_summarize_truncates_long_strings() -> None:
    result = _summarize({"key": "a" * 300})
    assert len(result["key"]) == 203
    assert result["key"].endswith("...")


def test_summarize_short_strings_passthrough() -> None:
    result = _summarize({"key": "short"})
    assert result["key"] == "short"


def test_summarize_none() -> None:
    assert _summarize(None) == {}


def test_summarize_empty() -> None:
    assert _summarize({}) == {}


def test_tool_call_does_not_raise() -> None:
    tool_call("test_tool", {"arg": "val"}, True, 0.05)
