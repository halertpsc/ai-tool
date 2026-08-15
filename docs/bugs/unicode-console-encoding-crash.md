# Bug: UnicodeEncodeError crash on non-cp1252 model output (Windows)

## Status
Fixed on 2026-08-15 — found during manual feature testing against a live
vLLM server (`nvidia/Qwen3.6-35B-A3B-NVFP4`). Fix applied in
`vllm_cli/main.py` (see below); full test suite (113 tests) still passes.

## Summary
On Windows, when the terminal's active code page is `cp1252` (the default),
`vllm-cli` crashes with an unhandled `UnicodeEncodeError` any time the model's
output contains a character outside that code page — arrows (`→`), emoji
(`🚀`), certain CJK/typographic punctuation, etc. This model uses such
characters routinely, so the crash is easy to hit in normal use.

## Root cause
Output is written straight to `sys.stdout` (via `click.echo(...)` or
`sys.stdout.write(...)`) without forcing a UTF-8-capable encoding. On a
default Windows console, `sys.stdout.encoding` is `cp1252`, which cannot
represent most non-Latin-1 characters, so the write raises instead of
degrading gracefully.

## Reproduction
```
vllm-cli complete "Reply with exactly this text and nothing else: A -> B -> C" --max-tokens 1500 --no-stream
```

Result:
```
File "...\vllm_cli\commands\complete.py", line 88, in complete_cmd
    click.echo(text)
  ...
  File "...\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680' in position 1: character maps to <undefined>
```

Also reproducible via plain `print()`/`click.echo()` of any string containing
`→` (→) or similar in the same shell — confirms it's a console/stdout
encoding issue, not something specific to one code path.

## Affected sites
All places that write model-generated text directly to `stdout`:
- `vllm_cli/commands/complete.py:88` — `click.echo(text)`
- `vllm_cli/commands/chat.py:106` — `click.echo(reply)`
- `vllm_cli/commands/chat.py:125` (`_stream_reply`) — `sys.stdout.write(token)`
- `vllm_cli/agent.py:58` (`_sync_round`) — `click.echo(content)`
- `vllm_cli/agent.py:69` (`_stream_round.on_content`) — `sys.stdout.write(text)`
- `vllm_cli/sse.py:123` (`stream_to_stdout`) — `sys.stdout.write(token)`

## Related finding: silent input corruption (not just a crash)
While verifying the fix, found that `sys.stdin` has the same root cause on
the *input* side, but it doesn't crash — it silently corrupts. Piping
non-cp1252 text into `chat` (e.g. via `click.prompt`) gets each UTF-8 byte
mis-decoded as one cp1252 character (classic mojibake), before the CLI ever
sends it to the model. Confirmed independently of the model:

```python
# printf "rocket 🚀 arrow →\n" | python -c "..."
sys.stdin.readline()  # cp1252 stdin decodes U+1F680 (🚀, bytes F0 9F 9A 80)
                       # as 4 separate garbage chars: ð Ÿ š €
```

Same class of bug, same fix location, so it's addressed together below.

## Fix applied
`vllm_cli/main.py`, at module import time (covers both the `vllm-cli`
console-script entry point and `python -m vllm_cli`, before any command
runs):

```python
import sys

# Model I/O is UTF-8 and may contain characters outside the default Windows
# console code page (cp1252): output containing them would otherwise raise
# UnicodeEncodeError, and input containing them would otherwise be silently
# mis-decoded (each UTF-8 byte read back as a separate cp1252 character).
# Reconfigure stdio to UTF-8 so both directions round-trip correctly.
for _stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")
```

`hasattr` guards against streams that don't support `reconfigure()` (e.g.
some test-runner-substituted streams).

### Verification
- Original crash repro (`vllm-cli complete "... 🚀" --no-stream`) now exits 0
  and prints the emoji/arrow correctly.
- `chat` piped input containing 🚀/→ now round-trips correctly end to end —
  confirmed by redirecting output to a file and inspecting raw bytes
  (`\xf0\x9f\x9a\x80` / `\xe2\x86\x92`, i.e. correct UTF-8), independent of
  any terminal's own display rendering.
- Full test suite (`pytest tests/`) still passes: 113/113.

### Alternative / supplementary (not applied, noted for reference)
`PYTHONUTF8=1` or `PYTHONIOENCODING=utf-8` env vars achieve the same result
but rely on user/deployment setup rather than working out of the box; the
in-code fix above was preferred since it requires no user action.

## Suggested test coverage (not yet added)
A regression test that patches `sys.stdout`/`sys.stdin` to `cp1252`-encoded
streams and asserts that reading/writing a string containing `\U0001F680`
round-trips without raising, for at least one representative command (e.g.
`complete`).
