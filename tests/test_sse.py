import pytest

from vllm_cli.sse import parse_sse_stream


def lines(*data_payloads):
    result = []
    for payload in data_payloads:
        result.append(f"data: {payload}")
        result.append("")
    return iter(result)


def test_completions_text_delta():
    tokens = list(parse_sse_stream(lines('{"choices":[{"text":"Hello"}]}', "[DONE]")))
    assert tokens == ["Hello"]


def test_chat_content_delta():
    tokens = list(parse_sse_stream(lines(
        '{"choices":[{"delta":{"content":"Hi"}}]}',
        '{"choices":[{"delta":{"content":" there"}}]}',
        "[DONE]",
    )))
    assert tokens == ["Hi", " there"]


def test_skips_empty_lines():
    raw = iter(["", "", 'data: {"choices":[{"delta":{"content":"A"}}]}', "", "data: [DONE]"])
    tokens = list(parse_sse_stream(raw))
    assert tokens == ["A"]


def test_skips_sse_comments():
    raw = iter([
        ": keep-alive",
        'data: {"choices":[{"delta":{"content":"B"}}]}',
        "data: [DONE]",
    ])
    tokens = list(parse_sse_stream(raw))
    assert tokens == ["B"]


def test_stops_at_done_sentinel():
    tokens = list(parse_sse_stream(lines(
        '{"choices":[{"delta":{"content":"A"}}]}',
        "[DONE]",
        '{"choices":[{"delta":{"content":"B"}}]}',
    )))
    assert tokens == ["A"]


def test_skips_malformed_json():
    raw = iter(["data: not-json", "data: [DONE]"])
    assert list(parse_sse_stream(raw)) == []


def test_empty_delta_yields_nothing():
    tokens = list(parse_sse_stream(lines(
        '{"choices":[{"delta":{}}]}',
        "[DONE]",
    )))
    assert tokens == []


def test_no_choices_yields_nothing():
    tokens = list(parse_sse_stream(lines('{"choices":[]}', "[DONE]")))
    assert tokens == []


def test_multiple_tokens_across_chunks():
    tokens = list(parse_sse_stream(lines(
        '{"choices":[{"delta":{"content":"one"}}]}',
        '{"choices":[{"delta":{"content":" two"}}]}',
        '{"choices":[{"delta":{"content":" three"}}]}',
        "[DONE]",
    )))
    assert tokens == ["one", " two", " three"]
    assert "".join(tokens) == "one two three"
