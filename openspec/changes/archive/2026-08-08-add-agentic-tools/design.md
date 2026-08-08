## Context

vllm-cli is a thin `click`-based CLI over an OpenAI-compatible chat/completions API (vLLM or OpenRouter), implemented with `httpx`. Today `chat.py` runs a simple loop: read a line, send full history to `/v1/chat/completions`, print the reply. `client.py` builds payloads and (for streaming) delegates SSE parsing to `sse.py`, which currently only extracts `choices[0].delta.content` text tokens.

Adding tool use means the model can return `tool_calls` instead of (or alongside) content, and expects a follow-up request containing `role: "tool"` messages before it produces a final answer. Because tool calls can read/write the user's filesystem, hit the network, or run arbitrary shell commands, every call must be gated by an explicit, per-call user approval — this is a security control, not a UX nicety, and must be impossible to bypass via config or flags.

## Goals / Non-Goals

**Goals:**
- Support OpenAI-compatible `tools` / `tool_choice` request fields and `tool_calls` response handling in both streaming and non-streaming chat.
- Ship a small set of built-in tools covering the request: file read, file write, file edit (replace a text range/snippet), directory listing, URL fetch, and CLI command execution.
- Enforce a single, uniform approval gate that every tool call passes through, with no per-tool opt-out.
- Keep tool use fully opt-in (`--tools` flag / config) so default chat behavior is unchanged and non-interactive/non-tty usage doesn't silently hang on a prompt.

**Non-Goals:**
- No sandboxing/containerization of shell command execution beyond an optional working-directory scope — this is a local dev CLI, not a multi-tenant service.
- No support for parallel/concurrent tool-call execution in this iteration; tool calls in one model turn are approved and executed sequentially in the order returned.
- No persistence of approval decisions across sessions (e.g., a saved "always allow" list) — approval is prompted per call, per session at most.
- No MCP (Model Context Protocol) server integration — tools are built-in and in-process only.

## Decisions

### 1. Tool loop lives in `chat.py`, not `client.py`
`client.py` stays a thin HTTP/payload layer (mirrors its current role). A new orchestration loop in `chat.py` (or a new `vllm_cli/agent.py` it calls into) owns the "send request → inspect for tool_calls → approve/execute → append tool results → resend" cycle. `client.py` only needs to accept an optional `tools` list in `chat`/`chat_stream` and return/yield structured tool-call data alongside content.
- **Alternative considered**: push the loop into `VllmClient`. Rejected — `client.py` is transport-focused and tool execution/approval is a UI concern that belongs with the REPL.

### 2. Tool registry as plain Python functions + JSON schema, not a plugin system
`vllm_cli/tools/registry.py` holds a static list of `Tool(name, description, json_schema, handler)` entries built from the six built-ins. No dynamic plugin loading or third-party tool discovery in this iteration.
- **Alternative considered**: entry-point-based plugin system for extensibility. Rejected as premature — nothing in the request asks for third-party tools, and it adds surface area to secure.

### 3. Approval gate is a single chokepoint function
One function, `request_approval(tool_name, arguments) -> bool`, is called immediately before every tool handler runs, regardless of tool. It prints the tool name and formatted arguments and prompts via `click.confirm` (default No). No tool implementation may execute its effect before this returns `True`. This makes the gate trivially auditable — grep for handler invocations shows exactly one call site.
- **Alternative considered**: per-tool approval decorators. Rejected — decorators are easy to forget on a new tool; a single call site in the loop is harder to accidentally bypass.
- **Denial behavior**: on denial, the loop synthesizes a `role: "tool"` message with content like `"User denied this tool call."` and continues the conversation — the model sees the rejection and can adapt, rather than the session crashing.

### 4. Streaming tool-call accumulation
Streaming responses deliver `tool_calls` as index-addressed deltas (id, function.name, function.arguments fragments) across multiple SSE chunks, per the OpenAI streaming protocol. `sse.py` gains a mode that accumulates these fragments by index into complete `{id, name, arguments}` records once the stream's `finish_reason` is `tool_calls`, reusing the existing `parse_sse_stream` generator but yielding a structured event type (`content` vs `tool_call`) instead of only raw text.
- **Alternative considered**: disable streaming whenever tools are enabled. Rejected — plain assistant replies in an agentic session should still stream for responsiveness; only the tool-call-bearing turns need special handling, and those already print no content to stream.

### 5. CLI command execution uses `subprocess.run`, not a shell string
The `run_command` tool accepts an argv list (or a single string split with `shlex`) and runs it with `subprocess.run(..., capture_output=True, timeout=<configurable>, cwd=<scoped dir>)`. Output is truncated (e.g., 8000 chars) before being fed back to the model to avoid blowing context. `shell=False` by default; a `shell: true` argument is allowed but still passes through the same approval prompt showing the literal command string, so the user always sees exactly what will run.
- **Alternative considered**: always `shell=True` for convenience (pipes, redirects). Rejected as default because it enables shell-metacharacter surprises the approval prompt can't fully convey; kept as an explicit opt-in the model must request and the user must approve.

### 6. Filesystem tools scoped to a configurable working directory
`read_file`/`write_file`/`edit_file`/`list_dir` resolve paths relative to a working directory (default: CWD where `vllm-cli chat` was launched) and reject paths that resolve outside it (`..` traversal, absolute paths elsewhere) unless the user explicitly widens scope via `--tools-root`. This is a safety default, not a hard sandbox — approval prompts still show the resolved absolute path.

### 7. New config keys, additive only
`config.py` gains `tools` (bool, default false) and `tools-root` (path). Both follow the existing CLI-flag > env var > config-file precedence already implemented in `resolve_settings`. No changes to existing keys.

## Risks / Trade-offs

- [Risk] A user reflexively approves every prompt ("approval fatigue") → Mitigation: prompt always echoes the exact arguments (full command string / absolute file path / URL) so there's something concrete to read, not just a generic "allow tool?" toggle.
- [Risk] Streaming tool-call delta accumulation is fiddlier than non-streaming and easy to get subtly wrong (index reuse, partial JSON) → Mitigation: cover with unit tests using recorded multi-chunk fixtures; fall back to non-streaming for the tool-call turn if a provider's stream format deviates.
- [Risk] Shell execution tool is inherently dangerous even with approval (approval fatigue, destructive commands) → Mitigation: no elevated privileges beyond the invoking user's own shell access (nothing this tool can do that the user couldn't already do), truncate/timeout output, and require the working-directory scope by default.
- [Risk] Feeding large file contents or command output back as tool results can blow past model context limits → Mitigation: truncate tool outputs to a fixed character budget and note truncation explicitly in the returned content so the model knows it's partial.
- [Trade-off] Sequential (non-parallel) tool-call execution is simpler and keeps the approval UX linear (one prompt at a time) but is slower when a model requests several independent calls in one turn. Acceptable for a CLI's interactive pace.

## Migration Plan

Additive only — no existing command, flag, or config key changes behavior. Rollout is a single release: ship `--tools` behind opt-in, default off. No data migration; config file gains new optional keys that default to `false`/unset. Rollback is simply not passing `--tools`.

## Open Questions

- Should `run_command` support a per-call timeout override from the model, or only a fixed CLI-configured timeout? (Leaning fixed, configurable via `config set tools-timeout`, to keep the approval prompt predictable.)
- Should approved-once tool calls within the *same* multi-step tool loop (e.g., model calls `read_file` five times in a row) still prompt every time, or offer a session-scoped "approve all of this tool" shortcut? Proposal's requirement is per-call approval with no bypass, so default is to prompt every time; revisit only if user feedback demands it.
