## 1. Config Management

- [x] 1.1 Add `referer` and `title` to `VALID_KEYS`, `KEY_MAP`, `KEY_TYPES` in `vllm_cli/config.py`
- [x] 1.2 Add `VLLM_REFERER` and `VLLM_TITLE` to `ENV_MAP` in `vllm_cli/config.py`
- [x] 1.3 Verify `config set referer|title`, `config get referer|title` work via existing generic key handling
- [x] 1.4 Update `config show` key iteration so `referer`/`title` display unmasked (confirm no special-casing needed beyond the existing `api-key` mask check)

## 2. HTTP Client

- [x] 2.1 Add optional `referer: Optional[str] = None, title: Optional[str] = None` params to `VllmClient.__init__` in `vllm_cli/client.py`
- [x] 2.2 Attach `HTTP-Referer` header when `referer` is truthy
- [x] 2.3 Attach `X-Title` header when `title` is truthy
- [x] 2.4 Confirm headers are omitted entirely when both values are unset

## 3. CLI Core

- [x] 3.1 Add `--referer` and `--title` global options to the root `click` group in `vllm_cli/main.py`
- [x] 3.2 Store `referer`/`title` in `ctx.obj`
- [x] 3.3 Thread resolved `referer`/`title` settings through to `VllmClient` construction in `complete` and `chat` commands

## 4. Testing and Validation

- [x] 4.1 Unit test: `config set/get referer` and `config set/get title` round-trip
- [x] 4.2 Unit test: `resolve_settings()` applies CLI flag > env var > config file priority for `referer`/`title`
- [x] 4.3 Unit test: `VllmClient` sends `HTTP-Referer`/`X-Title` headers when configured, omits them when not
- [x] 4.4 Manual end-to-end test: `vllm-cli --url https://openrouter.ai/api --api-key <key> --model <slug> --referer https://example.com --title "My App" complete "hello"` against OpenRouter (note: `--url` must be `https://openrouter.ai/api`, not `.../api/v1` — the client appends `/v1/...` itself; the latter 404s from a doubled `/v1`)
