## 1. Project Setup

- [ ] 1.1 Initialize Python package structure (`vllm_cli/` with `__init__.py`, `__main__.py`, `pyproject.toml`)
- [ ] 1.2 Add dependencies to `pyproject.toml`: `click`, `httpx`, `rich`, `tomli` (Python < 3.11 backport)
- [ ] 1.3 Create `vllm-cli` entry point script in `pyproject.toml` `[project.scripts]`
- [ ] 1.4 Verify `pip install -e .` installs and `vllm-cli --help` runs

## 2. Config Management

- [ ] 2.1 Implement config file path resolution (XDG on Unix, APPDATA on Windows)
- [ ] 2.2 Implement `config_read()` and `config_write()` helpers using `tomllib`/`tomli`
- [ ] 2.3 Implement `config set <key> <value>` command with key validation
- [ ] 2.4 Implement `config get <key>` command
- [ ] 2.5 Implement `config show` command with masked `api-key` display via `rich` table
- [ ] 2.6 Implement environment variable override layer (`VLLM_URL`, `VLLM_MODEL`, `VLLM_API_KEY`)
- [ ] 2.7 Implement config resolution priority: CLI flag > env var > config file, with clear error when URL missing

## 3. CLI Core

- [ ] 3.1 Create root `click` group with `--url`, `--model`, `--api-key`, `--output`, `--version` global options
- [ ] 3.2 Wire global options into a shared context object (`click.pass_context`)
- [ ] 3.3 Validate `--output` accepts only `text` or `json`
- [ ] 3.4 Verify `vllm-cli --version` prints version and `vllm-cli unknown-cmd` exits with code 2

## 4. HTTP Client

- [ ] 4.1 Create `client.py` with `VllmClient` class wrapping `httpx.Client`
- [ ] 4.2 Implement `complete(prompt, **params)` method posting to `/v1/completions`
- [ ] 4.3 Implement `chat(messages, **params)` method posting to `/v1/chat/completions`
- [ ] 4.4 Implement `complete_stream()` and `chat_stream()` methods using `httpx` streaming + SSE parsing
- [ ] 4.5 Add connection error and non-2xx HTTP error handling with clear messages

## 5. Streaming (SSE)

- [ ] 5.1 Implement SSE line parser: extract `data:` payload, skip comments, detect `[DONE]`
- [ ] 5.2 Implement token-by-token stdout flush in streaming mode
- [ ] 5.3 Implement TTY detection: default to streaming when stdout is a TTY, non-streaming when piped
- [ ] 5.4 Handle mid-stream connection drop: print newline, error message, exit code 1

## 6. Complete Subcommand

- [ ] 6.1 Implement `complete` command with positional `PROMPT` argument (reads stdin if omitted)
- [ ] 6.2 Add `--max-tokens`, `--temperature`, `--top-p`, `--stop` (multiple) flags with validation
- [ ] 6.3 Add `--stream`/`--no-stream` flag wired to streaming client method
- [ ] 6.4 Print plain text or JSON based on `--output` flag

## 7. Chat Subcommand

- [ ] 7.1 Implement `chat` command REPL loop with `You: ` prompt using `click.prompt`
- [ ] 7.2 Maintain in-memory conversation history list for the session duration
- [ ] 7.3 Add `--system` flag to prepend system message to all requests
- [ ] 7.4 Add `--max-tokens`, `--temperature`, `--top-p` flags
- [ ] 7.5 Handle `exit`/`quit` input and `Ctrl+C`/`Ctrl+D` (EOFError) gracefully
- [ ] 7.6 Wire streaming output (default on TTY) for chat responses

## 8. Output Formatting

- [ ] 8.1 Implement TTY-aware output: use `rich` for display when stdout is a TTY
- [ ] 8.2 Label assistant responses with `Assistant:` prefix in chat mode
- [ ] 8.3 Ensure `--output json` prints raw API response JSON for scripting

## 9. Testing and Validation

- [ ] 9.1 Write unit tests for config resolution priority and file read/write
- [ ] 9.2 Write unit tests for SSE parser with various chunk boundaries
- [ ] 9.3 Write integration tests for `complete` and `chat` against a mock httpx server
- [ ] 9.4 Manual end-to-end test against a running vLLM instance
- [ ] 9.5 Test piped output mode produces plain text without ANSI codes
