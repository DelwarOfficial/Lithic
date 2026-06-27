from lithic.compression.headroom_adapter import HeadroomAdapter


def test_compresses_long_text() -> None:
    adapter = HeadroomAdapter()
    text = "\n".join(f"line {i}" for i in range(3000))
    out = adapter.compress_tool_output(text, max_chars=1000)
    assert len(out) <= 1200
    assert "[compressed" in out


def test_preserves_exact_errors() -> None:
    adapter = HeadroomAdapter()
    error = "ValueError: exact failure at src/app.py:10"
    text = ("noise\n" * 2000) + error + ("\nnoise" * 2000)
    out = adapter.compress_tool_output(text, max_chars=1500)
    assert error in out


def test_preserves_code_blocks() -> None:
    adapter = HeadroomAdapter()
    code = "```python\nraise RuntimeError('do not change')\n```"
    text = ("noise\n" * 2000) + code + ("\nnoise" * 2000)
    out = adapter.compress_tool_output(text, max_chars=2000)
    assert code in out


def test_short_text_passes_through() -> None:
    adapter = HeadroomAdapter()
    short = "Hello, world!"
    assert adapter.compress_tool_output(short, max_chars=8000) == short


def test_fallback_compress_respects_max_chars() -> None:
    adapter = HeadroomAdapter()
    text = "\n".join(f"line {i}" for i in range(5000))
    out = adapter.compress_tool_output(text, max_chars=500)
    assert len(out) <= 600


def test_compress_text_caches(monkeypatch) -> None:
    adapter = HeadroomAdapter()
    text = "\n".join(f"line {i}" for i in range(200))
    first = adapter.compress_text(text)
    second = adapter.compress_text(text)
    assert first == second


def test_compress_messages_uses_fallback_when_no_headroom(monkeypatch) -> None:
    adapter = HeadroomAdapter()
    monkeypatch.setattr(adapter, "_headroom_compress", None)
    messages = [{"role": "user", "content": "hello world"}]
    result = adapter.compress_messages(messages)
    assert result[0]["role"] == "user"
    assert result[0]["content"] == "hello world"
