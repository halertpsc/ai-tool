## Context

The tool registry (`vllm_cli/tools/registry.py`) is a static list of `Tool` dataclasses, each a `(tools_root, **arguments) -> str` handler invoked synchronously, once per approved tool call, inside `agent.py`'s `MAX_TOOL_ROUNDS`-bounded loop. Every existing handler is stateless and completes within a single call: it reads/writes one file, lists one directory, fetches one URL, or runs one subprocess to completion (or timeout). This design adds four stateless tools (`search_files`, `glob_files`, `patch_file`, plus reuse of existing scoping/truncation helpers) and one stateful capability (background process management) that breaks the "completes within a single call" assumption for the first time.

Constraints carried over from the existing implementation and specs:
- All filesystem-touching tools resolve paths via `resolve_scoped_path` and reject anything outside `tools_root` (`agent-tools` spec).
- Every tool call, with no exceptions or bypass flags, goes through `request_approval` before its handler runs (`tool-approval` spec).
- Tool output is truncated to `MAX_OUTPUT_CHARS` (8000) with an explicit truncation notice.
- No third-party dependencies exist today beyond `click`, `httpx`, `rich`, `tomli`. The proposal commits to adding none for this change.
- The environment this ships on includes Windows, where `select()` does not work on pipe objects — this rules out a single-threaded non-blocking-read approach for process output.

## Goals / Non-Goals

**Goals:**
- Let the model search file contents and file names without shelling out through `run_command`.
- Let the model apply several edits to one file in a single approved call instead of one approval round-trip per hunk.
- Let the model start a long-running process (dev server, watcher), come back across several later turns to read its accumulated output, feed it input, and stop it when done.
- Keep every new tool consistent with existing conventions: `tools_root` scoping, mandatory per-call approval, fixed-size output truncation, no new dependencies.

**Non-Goals:**
- Real web search (deferred to a follow-up change; needs a decision on search provider and API key handling that's out of scope here).
- Unified-diff/fuzzy patch application — `patch_file` uses the same exact-substring-match semantics as the existing `edit_file`, just batched.
- Relaxing the per-call approval gate for polling calls (`read_process_output`) — out of scope; this change does not touch `tool-approval`.
- Persisting background processes across CLI restarts — process state is in-memory only, scoped to one CLI session.

## Decisions

### Content and file-pattern search implemented in pure Python, not by shelling out to `grep`/`ripgrep`
`search_files` and `glob_files` walk `tools_root` with `os.walk`/`pathlib` and match with `re`/`fnmatch`, rather than invoking an external `grep`/`rg`/`find` binary via subprocess.
- **Alternative considered**: shell out to `ripgrep`. Rejected — `rg` isn't guaranteed to be installed (especially on the Windows environment this ships on), and every other built-in tool today has zero external-binary dependencies; `run_command` exists precisely so the *model* can reach for a binary if one happens to be present, but a built-in tool shouldn't silently depend on one.
- Default excludes: `.git`, `__pycache__`, `node_modules`, `.venv`, `dist`, `build` (mirrors common `.gitignore`-style noise; not full `.gitignore` parsing, which would be a much larger feature).
- Binary files are skipped via a cheap null-byte sniff on the first chunk read.
- Results are capped (e.g. 200 matches) in addition to the standard character-based truncation, since a huge match count is more useful summarized than cut off mid-file.

### `patch_file` batches exact-match hunks instead of parsing unified diffs
`patch_file(path, edits: [{old_text, new_text}, ...])` applies each hunk in sequence against an in-memory copy of the file content — same uniqueness rule as `edit_file` (each `old_text` must match exactly once in the content *as of that point in the sequence*) — and only writes the file if every hunk in the list succeeds. On any hunk failing (not found, or ambiguous), no write occurs and the error identifies which hunk (by index) failed and why.
- **Alternative considered**: accept a unified diff string and apply it with context-line/offset matching (like `git apply`/`patch`). Rejected for this change — it requires fuzzy context matching and produces ambiguous partial-application failure modes; exact-match batched hunks keep the same predictable semantics `edit_file` already has, just applied N times atomically. Revisit if models struggle to produce well-scoped `old_text` snippets in practice.

### Background processes: in-memory registry with dedicated reader threads
A new `vllm_cli/tools/process.py` module keeps a module-level `dict[int, ProcessHandle]` (sequential integer IDs, not UUIDs — small numbers are easier for the model to reference in follow-up calls within the same session). `start_process` spawns via `subprocess.Popen` (cwd scoped to `tools_root`, same non-shell-by-default posture as `run_command`) and starts two daemon threads, one per stream, each blocked in a loop on `pipe.readline()` appending decoded lines into a lock-protected rolling buffer capped at a fixed size (same truncation convention as `MAX_OUTPUT_CHARS`, just applied continuously instead of once).
- **Why threads instead of `select`/`selectors`**: `select()` cannot poll pipe (non-socket) file objects on Windows, and this CLI runs there. Blocking reader threads per stream is the standard cross-platform pattern and needs no new dependency.
- `read_process_output(process_id)` returns everything accumulated since the last read (buffer is drained on read) plus liveness/exit-code status; it does not block waiting for new output.
- `send_process_input(process_id, text)` writes to `proc.stdin` and flushes.
- `stop_process(process_id)` calls `terminate()`, waits briefly, and escalates to `kill()` if still alive.
- A concurrency cap (e.g. 5 live background processes) makes `start_process` fail closed with an error result once exceeded, rather than letting the model spawn unbounded children.
- An `atexit` hook terminates all still-registered live processes when the CLI process exits normally, so a finished chat session doesn't leak children. This does not cover the process being killed ungracefully (e.g. SIGKILL/Windows force-close) — documented as a known limitation, not solved here.

### Every new tool stays inside the existing approval gate unmodified
No new tool bypasses or batches approval, including `read_process_output` polling calls. This is a deliberate acceptance of extra approval-prompt volume (flagged in the proposal's Impact section) rather than a special case, to keep `tool-approval`'s "no bypass, ever" invariant intact. If this proves too noisy in practice, that's a separate change against the `tool-approval` spec, not something to fold in here.

## Risks / Trade-offs

- **[Risk]** Pure-Python tree walk for `search_files` is slower than `ripgrep` on large repos. → **Mitigation**: default noise-directory excludes plus a match-count cap keep typical calls fast; documented as a known ceiling rather than optimized further in this change.
- **[Risk]** Long-lived background processes (e.g. a chatty dev server) could grow their output buffer unbounded between polls. → **Mitigation**: buffer is a rolling cap (oldest data dropped), same spirit as existing `truncate_output`, not an unbounded list.
- **[Risk]** A crashed or force-killed CLI session leaves orphaned child processes the `atexit` hook never runs for. → **Mitigation**: documented limitation; acceptable because it matches how any terminal-launched background process behaves without a supervisor, not a regression this change introduces.
- **[Risk]** `patch_file`'s sequential-hunk semantics mean hunk order matters if two hunks touch overlapping text. → **Mitigation**: validate-then-abort-on-first-failure with a clear per-index error message; no partial writes ever happen.

## Migration Plan

Purely additive — new modules, new entries in `registry.py`, new tests. No changes to existing tool behavior, config schema, or stored state. Nothing to migrate or roll back beyond normal code review/revert.

## Open Questions

- Should `read_process_output` polling eventually get a lighter-weight approval path (e.g. approve once per process, not per poll)? Deferred — would be a `tool-approval` spec change, out of scope here.
- Real web search backend and API-key handling — deferred to a follow-up change (this session's decision).
