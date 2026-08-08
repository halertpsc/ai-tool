## Why

vllm-cli already speaks a generic OpenAI-compatible protocol (configurable base URL, Bearer `api-key`), so basic chat/completion requests to OpenRouter's endpoint already succeed. The remaining gap is OpenRouter's optional attribution headers (`HTTP-Referer`, `X-Title`), which OpenRouter uses to identify the calling app for its rankings/leaderboards — there's currently no way to set them.

## What Changes

- Add `referer` and `title` config keys (config file, `VLLM_REFERER`/`VLLM_TITLE` env vars, `--referer`/`--title` global CLI flags) that, when set, are sent as `HTTP-Referer` and `X-Title` request headers on every API call.
- Model selection remains config/flag-driven only (`model` key / `--model` flag) — no model listing or discovery is added.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `config-management`: add `referer` and `title` as new optional configuration keys, resolved with the same CLI flag > env var > config file priority as existing keys.
- `cli-core`: add `--referer` and `--title` global options, threaded through to the HTTP client.

## Impact

- `vllm_cli/config.py`: extend `VALID_KEYS`, `KEY_MAP`, `KEY_TYPES`, `ENV_MAP` with `referer`/`title`.
- `vllm_cli/client.py`: accept optional `referer`/`title` and attach them as `HTTP-Referer`/`X-Title` headers when present.
- `vllm_cli/main.py`: add `--referer`/`--title` global flags, wire into context.
- `vllm_cli/commands/config_cmd.py`: no new secrets to mask; `referer`/`title` show as plain values in `config show`.
- Tests: unit tests for new config keys and header attachment.
