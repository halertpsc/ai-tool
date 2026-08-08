## 1. Config and CLI flags

- [x] 1.1 Add `tools` (bool) and `tools-root` (path) to `VALID_KEYS`, `KEY_MAP`, `KEY_TYPES`, and `ENV_MAP` (`VLLM_TOOLS`, `VLLM_TOOLS_ROOT`) in `vllm_cli/config.py`
- [x] 1.2 Add `--tools` and `--tools-root <dir>` options to the `chat` command in `vllm_cli/commands/chat.py`, resolved through `resolve_settings` with the existing CLI-flag > env > config precedence
- [x] 1.3 Update `vllm_cli/commands/config_cmd.py` help/validation text to include the two new keys

## 2. Tool approval gate

- [x] 2.1 Create `vllm_cli/tools/approval.py` with `request_approval(tool_name: str, arguments: dict) -> bool` that prints the tool name and formatted arguments and calls `click.confirm(default=False)`
- [x] 2.2 Make `request_approval` detect a non-interactive session (stdin/stdout not a TTY) and return `False` immediately without prompting
- [x] 2.3 Ensure there is exactly one call site for `request_approval` in the agentic loop (task 5.3) so every tool execution path passes through it — no per-tool bypass

## 3. Tool registry and built-in tools

- [x] 3.1 Create `vllm_cli/tools/registry.py` defining a `Tool` dataclass (`name`, `description`, `parameters` JSON Schema, `handler`) and a `BUILTIN_TOOLS` list
- [x] 3.2 Implement `read_file(path)` in `vllm_cli/tools/files.py`, resolving against the tools root and returning file content or an error string
- [x] 3.3 Implement `write_file(path, content)` in `vllm_cli/tools/files.py`, creating parent directories as needed
- [x] 3.4 Implement `edit_file(path, old_text, new_text)` in `vllm_cli/tools/files.py`, failing with an error result on zero or multiple matches of `old_text`
- [x] 3.5 Implement `list_dir(path)` in `vllm_cli/tools/files.py`, returning direct entry names
- [x] 3.6 Implement a shared `resolve_scoped_path(tools_root, path)` helper in `vllm_cli/tools/files.py` that rejects paths resolving outside `tools_root`, used by 3.2–3.5
- [x] 3.7 Implement `fetch_url(url)` in `vllm_cli/tools/web.py` using `httpx`, rejecting non-`http(s)` schemes and truncating the response body to a fixed max length
- [x] 3.8 Implement `run_command(argv, shell=False)` in `vllm_cli/tools/shell.py` using `subprocess.run` with `cwd` scoped to the tools root, a configurable timeout, and truncated stdout/stderr in the result
- [x] 3.9 Add a shared `truncate_output(text, max_chars)` helper used by 3.2, 3.7, and 3.8, appending an explicit truncation notice when applied
- [x] 3.10 Wire `BUILTIN_TOOLS` entries to their handlers and JSON Schema parameter definitions for all six tools

## 4. Protocol support for tool calls

- [x] 4.1 Extend `VllmClient._chat_payload` to accept and include `tools` and optional `tool_choice` when provided
- [x] 4.2 Update `VllmClient.chat` to return `tool_calls` from the response alongside existing content, when present (satisfied by the existing full-response-dict return — `message.tool_calls` is already present when the API returns it, no extraction needed)
- [x] 4.3 Extend `vllm_cli/sse.py` to parse `delta.tool_calls` fragments (index, id, function.name, function.arguments) in addition to `delta.content`, yielding structured events distinguishing content tokens from tool-call fragments (new `parse_sse_events`, kept separate from `parse_sse_stream` to preserve its existing plain-text-token behavior/tests)
- [x] 4.4 Add tool-call fragment accumulation by index in `sse.py` (or a new helper), assembling complete `{id, name, arguments}` records once the stream's `finish_reason` is `tool_calls` (`collect_stream`)
- [x] 4.5 Update `VllmClient.chat_stream` to yield accumulated tool-call events as well as content tokens (added `chat_stream_events`, used by the agentic loop; `chat_stream` unchanged for the non-agentic path)

## 5. Chat REPL agentic loop

- [x] 5.1 Create `vllm_cli/agent.py` with an `AgentLoop` (or equivalent function) that: sends the request with `tools` when agentic mode is enabled, inspects the response for tool calls, and drives the approve/execute/append/resend cycle until a reply has no tool calls
- [x] 5.2 Implement tool-call argument JSON parsing with a clear error path (malformed arguments become an error tool-result, not a crash)
- [x] 5.3 Call `request_approval` (task 2.1) before invoking each tool handler; on denial, append a `role: "tool"` message stating the call was denied and skip execution
- [x] 5.4 Process multiple tool calls within one model turn sequentially, in the order returned
- [x] 5.5 Integrate `AgentLoop` into `vllm_cli/commands/chat.py`'s REPL, active only when `--tools`/`tools` config is enabled; unchanged behavior when disabled
- [x] 5.6 Ensure streaming sessions accumulate tool calls fully (task 4.4) before entering the approval flow, per turn

## 6. Tests

- [x] 6.1 Unit tests for `resolve_scoped_path` covering in-scope paths, `..` traversal rejection, and absolute-path rejection
- [x] 6.2 Unit tests for each built-in tool handler (success and error paths), including `edit_file` ambiguous/missing snippet cases and `run_command` timeout handling
- [x] 6.3 Unit tests for `request_approval`: approved, denied, and non-interactive (no TTY) cases
- [x] 6.4 Unit tests for SSE tool-call delta accumulation using recorded multi-chunk fixtures
- [x] 6.5 Integration test for the agentic loop: mock client returns a tool call, approval is stubbed to approve/deny, assert correct tool-result message is appended and looped
- [x] 6.6 Regression test confirming `chat` behavior is unchanged when `--tools` is not passed (no `tools` field sent, no approval prompts)

## 7. Docs

- [x] 7.1 Update `README.md` with `--tools`/`--tools-root` usage, the list of built-in tools, and an explanation of the mandatory approval prompt
