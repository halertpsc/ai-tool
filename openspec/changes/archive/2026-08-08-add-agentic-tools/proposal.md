## Why

vllm-cli currently only relays chat turns between the user and the model — it cannot read/write files, fetch web content, or run commands on the user's behalf. Most modern chat-completion APIs (OpenAI-compatible `tools`/`tool_calls`) support function calling, and users want the CLI to act as a lightweight coding/ops agent. Without an explicit human approval gate, letting a model execute file edits or shell commands is unsafe, so approval must be a first-class, non-bypassable part of the design.

## What Changes

- Add a tool registry with built-in tools: read file, write file, edit (find/replace or patch) file, list/glob directory, fetch a URL, and run a CLI command.
- Add a mandatory approval gate: every single tool-call attempt is presented to the user (tool name + arguments) and requires explicit approval before it executes; denial returns a tool-result telling the model the call was rejected instead of executing it.
- Extend the chat REPL so it can send tool schemas to the model, parse `tool_calls` from both streaming and non-streaming responses, run the approval + execution loop, feed `tool` role results back, and continue until the model returns a plain assistant message.
- Add a `--tools` / config flag to enable agentic mode for a chat session (off by default) and, for the CLI-exec tool, an optional working-directory scope.
- **BREAKING**: none — tool use is opt-in via a flag; default chat behavior is unchanged.

## Capabilities

### New Capabilities
- `agent-tools`: Built-in tool registry (file read/write/edit, directory listing, web fetch, CLI command execution) exposed to the model as OpenAI-compatible tool schemas, plus the sandboxing/output-size rules each tool follows.
- `tool-approval`: Cross-cutting human-in-the-loop gate that intercepts every tool-call attempt from any tool, shows the user what will run, and only executes on explicit per-call approval.

### Modified Capabilities
- `chat`: The chat REPL gains an opt-in agentic mode that sends tool schemas with each request, handles multi-turn tool-call/tool-result exchanges (streaming and non-streaming), and loops until a final assistant reply.

## Impact

- `vllm_cli/client.py`: payload builders gain `tools`/`tool_choice`; response handling must extract `tool_calls` (non-streaming) and accumulate tool-call deltas (streaming).
- `vllm_cli/sse.py`: SSE parsing must surface tool-call delta chunks, not just content tokens.
- `vllm_cli/commands/chat.py`: REPL loop drives the approve → execute → feed-result-back cycle; add `--tools` flag.
- New module `vllm_cli/tools/` (registry, individual tool implementations, approval prompt).
- `vllm_cli/config.py`: new settings for enabling tools by default and scoping the CLI-exec/file tools to a working directory.
- New dependency: an HTTP client for web fetch (reuse `httpx`, already a dependency).
