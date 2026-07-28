## Context

vLLM exposes an OpenAI-compatible REST API (`/v1/completions`, `/v1/chat/completions`). There is no dedicated CLI for it — users rely on curl or custom scripts. This design covers a Python CLI tool that wraps those endpoints with a clean UX, persistent configuration, and streaming support.

The project is a new standalone tool with no existing codebase to migrate.

## Goals / Non-Goals

**Goals:**
- Single-turn completions via `vllm-cli complete "<prompt>"`
- Interactive chat sessions via `vllm-cli chat`
- Config management via `vllm-cli config set/get/show`
- Streaming output (token-by-token) for both modes
- Plain-text and JSON output modes for scripting

**Non-Goals:**
- Model management (loading, unloading, health-checking vLLM infrastructure)
- Multi-server load balancing or failover
- Authentication/API-key management beyond passing a bearer token
- GUI or TUI beyond simple ANSI-colored terminal output

## Decisions

### 1. HTTP client: `httpx` over `requests`

`httpx` supports async streaming natively and has an identical sync API to `requests`. Streaming SSE responses from vLLM require iterable chunked responses; `httpx` handles this cleanly. `requests` requires manual `iter_lines()` with `stream=True` and is not async-capable if we need to add async support later.

**Alternative considered**: `aiohttp` — async-first but requires an event loop for all usage, complicates the sync CLI path.

### 2. CLI framework: `click` over `argparse`

`click` provides composable command groups, automatic help generation, and built-in type validation with less boilerplate. The subcommand structure (`complete`, `chat`, `config`) maps directly to click command groups.

**Alternative considered**: `argparse` — stdlib, no dependency, but verbose for nested subcommands and lacks built-in color/prompt support.

### 3. Config file: TOML at `~/.config/vllm-cli/config.toml`

TOML is human-readable, supports comments, and is parseable with stdlib `tomllib` (Python 3.11+) or `tomli` backport. Stored at XDG config path for Unix compatibility; falls back to `%APPDATA%\vllm-cli\config.toml` on Windows.

**Alternative considered**: JSON — no comments, less ergonomic for manual editing. INI — limited nesting for future extension.

### 4. Output rendering: `rich` for interactive, raw for piped output

When stdout is a TTY, use `rich` for markdown rendering, syntax highlighting, and spinner during non-streaming waits. When stdout is piped, output plain text or JSON depending on `--output` flag. This follows the principle of least surprise for scripting.

### 5. Streaming: SSE via `httpx` chunked response

vLLM's streaming endpoint returns Server-Sent Events (`data: {...}\n\n`). Parse each `data:` line, decode JSON, and print the delta token. On `[DONE]` sentinel, end the stream.

## Risks / Trade-offs

- **vLLM API version drift** → Pin to OpenAI-compatible endpoints which vLLM commits to maintaining; surface clear errors when response shape is unexpected.
- **Windows terminal streaming flicker** → Use `rich.live` with a buffer; flush only on newlines when not in a TTY.
- **Large context in chat mode** → No automatic truncation; user is responsible. Document token limits clearly. Future: add `--max-history-tokens` flag.
- **No retry logic** → Network errors surface immediately. Acceptable for a developer tool; add `--retry N` as a follow-up.

## Migration Plan

New standalone tool — no migration required. Install via `pip install vllm-cli` (or `pipx install vllm-cli`). Config file is created on first `vllm-cli config set` or first run with `--url`.

## Open Questions

- Should `chat` mode support saving/loading named sessions? (defer to v2)
- Should we support the `/v1/models` endpoint to list available models? (nice-to-have, add as `vllm-cli models` in a follow-up)
