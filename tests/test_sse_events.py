from vllm_cli.sse import collect_stream, parse_sse_events


def lines(*data_payloads):
    result = []
    for payload in data_payloads:
        result.append(f"data: {payload}")
        result.append("")
    return iter(result)


def test_parse_sse_events_content_only():
    events = list(parse_sse_events(lines(
        '{"choices":[{"delta":{"content":"Hi"}}]}',
        "[DONE]",
    )))
    assert events == [{"type": "content", "text": "Hi"}]


def test_parse_sse_events_tool_call_delta():
    events = list(parse_sse_events(lines(
        '{"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1",'
        '"function":{"name":"read_file","arguments":""}}]}}]}',
        '{"choices":[{"delta":{"tool_calls":[{"index":0,'
        '"function":{"arguments":"{\\"path\\""}}]}}]}',
        '{"choices":[{"delta":{"tool_calls":[{"index":0,'
        '"function":{"arguments":": \\"a.txt\\"}"}}]}}]}',
        '{"choices":[{"delta":{},"finish_reason":"tool_calls"}]}',
        "[DONE]",
    )))
    tool_events = [e for e in events if e["type"] == "tool_call_delta"]
    assert len(tool_events) == 3
    assert tool_events[0]["id"] == "call_1"
    assert tool_events[0]["name"] == "read_file"
    finish_events = [e for e in events if e["type"] == "finish"]
    assert finish_events == [{"type": "finish", "reason": "tool_calls"}]


def test_collect_stream_accumulates_content():
    events = parse_sse_events(lines(
        '{"choices":[{"delta":{"content":"one"}}]}',
        '{"choices":[{"delta":{"content":" two"}}]}',
        "[DONE]",
    ))
    seen = []
    result = collect_stream(events, on_content=seen.append)
    assert result["content"] == "one two"
    assert result["tool_calls"] == []
    assert seen == ["one", " two"]


def test_collect_stream_accumulates_tool_call_across_chunks():
    events = parse_sse_events(lines(
        '{"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1",'
        '"function":{"name":"read_file","arguments":""}}]}}]}',
        '{"choices":[{"delta":{"tool_calls":[{"index":0,'
        '"function":{"arguments":"{\\"path\\": "}}]}}]}',
        '{"choices":[{"delta":{"tool_calls":[{"index":0,'
        '"function":{"arguments":"\\"a.txt\\"}"}}]}}]}',
        '{"choices":[{"delta":{},"finish_reason":"tool_calls"}]}',
        "[DONE]",
    ))
    result = collect_stream(events)
    assert result["content"] == ""
    assert len(result["tool_calls"]) == 1
    call = result["tool_calls"][0]
    assert call["id"] == "call_1"
    assert call["name"] == "read_file"
    assert call["arguments"] == '{"path": "a.txt"}'
    assert result["finish_reason"] == "tool_calls"


def test_collect_stream_multiple_tool_calls_by_index():
    events = parse_sse_events(lines(
        '{"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1",'
        '"function":{"name":"read_file","arguments":"{}"}}]}}]}',
        '{"choices":[{"delta":{"tool_calls":[{"index":1,"id":"call_2",'
        '"function":{"name":"list_dir","arguments":"{}"}}]}}]}',
        "[DONE]",
    ))
    result = collect_stream(events)
    assert [c["id"] for c in result["tool_calls"]] == ["call_1", "call_2"]
    assert [c["name"] for c in result["tool_calls"]] == ["read_file", "list_dir"]
