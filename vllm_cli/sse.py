import json
import sys
from typing import Any, Callable, Dict, Generator, Iterable, Iterator, Optional


class StreamInterrupted(Exception):
    pass


def parse_sse_stream(lines: Iterator[str]) -> Generator[str, None, None]:
    """Parse SSE stream lines and yield delta token strings."""
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith(":"):
            continue
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            return
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        choices = chunk.get("choices", [])
        if not choices:
            continue
        choice = choices[0]
        # Support both /v1/completions ("text") and /v1/chat/completions ("delta.content")
        delta = choice.get("delta", {})
        text = delta.get("content") or choice.get("text") or ""
        if text:
            yield text


def parse_sse_events(lines: Iterator[str]) -> Generator[Dict[str, Any], None, None]:
    """Parse SSE stream lines and yield structured events, one of:
      {"type": "content", "text": str}
      {"type": "tool_call_delta", "index": int, "id": str|None, "name": str|None, "arguments": str|None}
      {"type": "finish", "reason": str|None}
    """
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith(":"):
            continue
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            return
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        choices = chunk.get("choices", [])
        if not choices:
            continue
        choice = choices[0]
        delta = choice.get("delta", {})

        text = delta.get("content") or choice.get("text") or ""
        if text:
            yield {"type": "content", "text": text}

        for tool_call in delta.get("tool_calls") or []:
            function = tool_call.get("function") or {}
            yield {
                "type": "tool_call_delta",
                "index": tool_call.get("index", 0),
                "id": tool_call.get("id"),
                "name": function.get("name"),
                "arguments": function.get("arguments"),
            }

        finish_reason = choice.get("finish_reason")
        if finish_reason:
            yield {"type": "finish", "reason": finish_reason}


def collect_stream(
    events: Iterable[Dict[str, Any]],
    on_content: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Consume structured SSE events, accumulating content and tool-call
    argument fragments (addressed by index) into complete records.

    Returns {"content": str, "tool_calls": [{"id", "name", "arguments"}, ...],
    "finish_reason": str|None}.
    """
    content_parts = []
    calls: Dict[int, Dict[str, Any]] = {}
    finish_reason = None

    for event in events:
        etype = event["type"]
        if etype == "content":
            content_parts.append(event["text"])
            if on_content:
                on_content(event["text"])
        elif etype == "tool_call_delta":
            index = event["index"]
            entry = calls.setdefault(index, {"id": None, "name": "", "arguments": ""})
            if event.get("id"):
                entry["id"] = event["id"]
            if event.get("name"):
                entry["name"] += event["name"]
            if event.get("arguments"):
                entry["arguments"] += event["arguments"]
        elif etype == "finish":
            finish_reason = event["reason"]

    return {
        "content": "".join(content_parts),
        "tool_calls": [calls[index] for index in sorted(calls)],
        "finish_reason": finish_reason,
    }


def stream_to_stdout(tokens: Generator[str, None, None]) -> None:
    """Print tokens one-by-one with immediate flush."""
    try:
        for token in tokens:
            sys.stdout.write(token)
            sys.stdout.flush()
        sys.stdout.write("\n")
        sys.stdout.flush()
    except Exception as exc:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise StreamInterrupted(str(exc)) from exc
