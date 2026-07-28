import json
import sys
from typing import Generator, Iterator


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
