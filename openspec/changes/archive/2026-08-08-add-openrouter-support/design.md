## Context

vllm-cli's `VllmClient` (`vllm_cli/client.py`) already builds a generic `Authorization: Bearer` header from an `api_key` and posts OpenAI-schema payloads to a configurable `base_url`. Config resolution (`vllm_cli/config.py`) already supports the CLI flag > env var > config file priority for `url`, `model`, `api-key`. OpenRouter's API (`https://openrouter.ai/api/v1`) is OpenAI-compatible and requires no changes beyond this — the only OpenRouter-specific piece missing is its two optional attribution headers, `HTTP-Referer` and `X-Title`, which OpenRouter uses to identify the calling application for its public rankings.

## Goals / Non-Goals

**Goals:**
- Let a user configure `referer` and `title` values that get sent as `HTTP-Referer`/`X-Title` headers on every request, following the exact same resolution mechanism (CLI flag > env var > config file) already used for `url`/`model`/`api-key`.
- Keep both values fully optional — omit the headers entirely when unset, so behavior against non-OpenRouter servers (plain vLLM) is unchanged.

**Non-Goals:**
- No model listing/discovery command. Model selection stays exactly as it is today: `model` config key / `--model` flag only.
- No OpenRouter-specific routing features (provider preferences, fallback models, `route` field, cost/usage reporting) — out of scope for this change.
- No renaming of the CLI or its `VLLM_*` env var prefix; it remains a generic OpenAI-compatible client that happens to also work with OpenRouter.

## Decisions

- **Reuse the existing config plumbing.** Add `referer` and `title` to `VALID_KEYS`, `KEY_MAP`, `KEY_TYPES`, `ENV_MAP` in `config.py` exactly like the other string keys, rather than inventing a parallel mechanism. This keeps `config set/get/show` and env override behavior consistent for free.
  - Alternative considered: a separate `--header key=value` generic passthrough flag. Rejected as broader than what's needed and harder to validate/mask consistently; can be added later if more providers need arbitrary headers.
- **New env vars `VLLM_REFERER` / `VLLM_TITLE`**, matching the existing `VLLM_URL`/`VLLM_MODEL`/`VLLM_API_KEY` naming convention rather than an `OPENROUTER_*` prefix, since the client remains provider-agnostic.
- **`VllmClient.__init__` gains optional `referer: Optional[str] = None, title: Optional[str] = None` params.** Headers are only added to the `httpx.Client` when the values are truthy, mirroring the existing `api_key` handling.
- **Global CLI flags `--referer`/`--title`** added to the root `click` group alongside `--url`/`--model`/`--api-key`, stored in `ctx.obj`, and passed into `resolve_settings()`/`VllmClient(...)` the same way `api-key` currently is.

## Risks / Trade-offs

- [Header names could be mistaken for secrets] → `referer`/`title` are not treated as sensitive; `config show` displays them in plain text (unlike `api-key`, which is masked). This matches OpenRouter's own docs, which describe these as public identifying values, not credentials.
- [Scope creep toward a full "provider" abstraction] → Explicitly kept out of scope; this change only adds two optional headers, not a provider/preset system.
