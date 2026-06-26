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
