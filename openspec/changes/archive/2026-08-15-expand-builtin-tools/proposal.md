## Why

The built-in tool registry only supports whole-file reads, single-hunk exact-text edits, one-level directory listing, and a synchronous subprocess runner. This forces the model to fall back on manually shelling out through `run_command` for tasks that should be first-class tool calls (finding where something is defined, discovering files by name pattern), makes multi-location edits take one round-trip per hunk, and makes it impossible to work with anything long-running (a dev server, a watcher, a REPL) since `run_command` blocks until the process exits or times out.

## What Changes

- Add `search_files`: grep-equivalent regex content search across files under the tools working directory, returning `path:line:match` results with optional include/exclude glob filtering and a capped result count.
- Add `glob_files`: pattern-based file discovery (e.g. `**/*.py`) under the tools working directory, returning matching relative paths.
- Add `patch_file`: apply multiple exact-match `old_text`/`new_text` hunks to a single file in one call, validated and applied atomically (all hunks succeed or none are written) — extends the existing single-hunk `edit_file` pattern to multi-hunk without introducing unified-diff parsing.
- Add background process management tools — `start_process`, `list_processes`, `read_process_output`, `send_process_input`, `stop_process` — to launch a subprocess that keeps running across multiple tool-call turns, poll its accumulated stdout/stderr, write to its stdin, and terminate it on demand.
- All new tools reuse the existing conventions unmodified: scoped to the tools working directory, gated by the mandatory per-call approval prompt, and output truncated to the fixed size limit.
- Out of scope for this change: a real web search tool (no discovery tool for unknown URLs) — deferred to a follow-up change pending a decision on search provider/API key handling.

## Capabilities

### New Capabilities
- `background-processes`: Launching, listing, polling output from, writing input to, and stopping subprocesses that persist across multiple tool-call turns instead of running to completion within a single call.

### Modified Capabilities
- `agent-tools`: Add `search_files`, `glob_files`, and `patch_file` tool requirements to the built-in registry; extend the existing working-directory scoping and output-truncation requirements to explicitly cover the new tools.

## Impact

- `vllm_cli/tools/`: new modules for content search, glob search, and multi-hunk patching; new module for process lifecycle management; additions to `registry.py` to expose the new tool schemas.
- No new third-party dependencies — content search, globbing, and process management are all achievable with the standard library (`re`, `glob`/`pathlib`, `subprocess`, `threading`).
- `tests/`: new test files mirroring the existing `test_tools_files.py` / `test_tools_shell.py` pattern.
- Approval prompts will fire more often in practice, since polling a background process's output is itself a tool call subject to the existing mandatory per-call approval gate (no change to that gate's behavior, just more frequent use of it).
