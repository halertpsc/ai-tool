## Why

Developers and researchers running models on vLLM lack a dedicated CLI tool to interact with hosted models — they must write custom scripts or use generic HTTP clients. A purpose-built CLI provides a fast, scriptable, and human-friendly interface for querying vLLM endpoints without boilerplate.

## What Changes

- New standalone CLI tool (`vllm-cli`) for sending prompts to vLLM-hosted models via its OpenAI-compatible API
- Support for single-turn completions and interactive chat (multi-turn) sessions
- Configuration management for server URL, model name, and generation parameters
- Streaming output support for real-time token display
- JSON and plain-text output modes for scripting integration

## Capabilities

### New Capabilities

- `cli-core`: Entry point, argument parsing, and command dispatch (subcommands: `chat`, `complete`, `config`)
- `completion`: Single-turn text completion against a vLLM endpoint
- `chat`: Interactive multi-turn chat session with conversation history management
- `config-management`: Persistent configuration (server URL, model, default params) via a local config file
- `streaming`: Streaming response support for both completion and chat modes

### Modified Capabilities

<!-- none -->

## Impact

- New Python package/script; no existing code modified
- Depends on vLLM's OpenAI-compatible REST API (`/v1/completions`, `/v1/chat/completions`)
- Runtime dependencies: `httpx` or `requests` for HTTP, `rich` for terminal output, `click` or `argparse` for CLI
- No database or auth requirements — purely stateless except for local config file
