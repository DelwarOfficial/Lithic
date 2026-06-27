from lithic.tools.audit import _redact, _redact_obj


def test_redact_secrets() -> None:
    assert "***" in _redact("api_key=sk-1234567890")
    assert "***" in _redact('Authorization: Bearer tok_xyz')


def test_redact_dict() -> None:
    obj = {"api_key": "sk-secret", "name": "hello"}
    redacted = _redact_obj(obj)
    assert redacted["api_key"] == "***"
    assert redacted["name"] == "hello"


def test_redact_list() -> None:
    obj = ["api_key=sk-123", "safe"]
    redacted = _redact_obj(obj)
    assert "***" in str(redacted[0])
    assert redacted[1] == "safe"


def test_redact_nested() -> None:
    obj = {"config": {"token": "t0ken"}}
    redacted = _redact_obj(obj)
    assert redacted["config"]["token"] == "***"
