# vllm-cli

Command-line interface for vLLM-hosted (or other OpenAI-compatible) models.

## Commands

- `vllm-cli complete "<prompt>"` — single-shot completion
- `vllm-cli chat` — interactive multi-turn chat session
- `vllm-cli config set|get|show` — manage persistent configuration

Configuration (server URL, model, API key, etc.) is resolved with priority
CLI flags > environment variables > config file (`vllm-cli config set ...`).

## Agentic tools

`vllm-cli chat` can optionally let the model call a small set of built-in
tools to read/write files, fetch web pages, and run CLI commands. This is
off by default.

```
vllm-cli chat --tools
vllm-cli chat --tools --tools-root ./my-project
```

Or persist it: `vllm-cli config set tools true` and
`vllm-cli config set tools-root /path/to/project` (env vars: `VLLM_TOOLS`,
`VLLM_TOOLS_ROOT`).

Built-in tools:

- `read_file` — read a file's contents
- `write_file` — create or overwrite a file
- `edit_file` — replace an exact, unique text snippet in a file
- `list_dir` — list a directory's entries
- `fetch_url` — HTTP GET an `http(s)://` URL
- `run_command` — run a CLI command as a subprocess

File and command tools are scoped to a working directory (`--tools-root`,
default: the directory you launched `vllm-cli` from) and refuse to touch
paths outside it.

**Every tool call requires your explicit approval.** Before any tool runs,
vllm-cli prints the tool name and its exact arguments (the resolved file
path, the literal command, the URL) and asks you to confirm. There is no
flag to bypass this — if you deny a call, the model is told the call was
denied and the conversation continues. In a non-interactive session (no
TTY), tool calls are automatically denied rather than silently approved.
