## 1. Content and glob search tools

- [x] 1.1 Create `vllm_cli/tools/search.py` with `search_files(tools_root, pattern, include=None, exclude=None)`: walk `tools_root`, skip default noise directories (`.git`, `__pycache__`, `node_modules`, `.venv`, `dist`, `build`) and binary files (null-byte sniff), apply include/exclude glob filters, return `path:line:content` matches capped at a fixed count, reject invalid regex with an error result.
- [x] 1.2 Add `glob_files(tools_root, pattern)` to `search.py`: reject patterns containing `..` segments, return sorted relative paths matching the pattern under `tools_root`, or a clear "no matches" result.
- [x] 1.3 Register `search_files` and `glob_files` tool schemas (name, description, JSON Schema parameters, handler) in `vllm_cli/tools/registry.py`.

## 2. Multi-hunk patch tool

- [x] 2.1 Add `patch_file(tools_root, path, edits)` to `vllm_cli/tools/files.py`: apply an ordered list of `{old_text, new_text}` hunks against an in-memory copy of the file content, validating each hunk's uniqueness at the point it's applied; write once only if all hunks succeed; on failure, make no change and return which hunk index failed and why.
- [x] 2.2 Register `patch_file` tool schema in `registry.py`.

## 3. Background process management

- [x] 3.1 Create `vllm_cli/tools/process.py` with a `ProcessHandle` record (Popen, command, started-at, rolling output buffer with lock, reader threads) and a module-level `dict[int, ProcessHandle]` registry keyed by a sequential ID counter; define the concurrency cap and output-buffer size as constants.
- [x] 3.2 Implement `start_process(tools_root, command, shell=False)`: spawn via `subprocess.Popen` with `cwd=tools_root`, reject if the concurrency cap is already reached, start one daemon reader thread per stream (stdout/stderr) that appends decoded lines into the bounded rolling buffer, and return the new process ID.
- [x] 3.3 Implement `list_processes(tools_root)`: return each tracked process's ID, original command, and running/exited status (with exit code if exited).
- [x] 3.4 Implement `read_process_output(tools_root, process_id)`: drain and return output accumulated since the last read (or since start), report current running status/exit code, note when buffered output was dropped due to the cap, and return an error for an unknown process ID.
- [x] 3.5 Implement `send_process_input(tools_root, process_id, text)`: write to the process's stdin and flush if still running; return an error result if the process has already exited.
- [x] 3.6 Implement `stop_process(tools_root, process_id)`: `terminate()`, wait a short grace period, escalate to `kill()` if still alive, and return a clear already-exited message (not an error) if the process had already finished.
- [x] 3.7 Register an `atexit` hook (in `process.py`, wired in at import or CLI entrypoint) that terminates every still-live tracked process on normal interpreter exit.
- [x] 3.8 Register `start_process`, `list_processes`, `read_process_output`, `send_process_input`, and `stop_process` tool schemas in `registry.py`.

## 4. Tests

- [x] 4.1 `tests/test_tools_search.py`: `search_files` — matches found, no matches, include/exclude filtering, default noise-directory exclusion, binary file skipped, match cap enforced, invalid regex rejected.
- [x] 4.2 `tests/test_tools_search.py`: `glob_files` — matches found, no matches, `..` traversal rejected.
- [x] 4.3 `tests/test_tools_files.py`: `patch_file` — all hunks applied in one write, a failing hunk aborts with no partial write and identifies the failing index.
- [x] 4.4 `tests/test_tools_process.py`: full lifecycle (start → list → read output → send input → stop), concurrency cap enforced, output buffer bound enforced with drop notice, reading output after process exit, stopping an already-exited process, unknown process ID errors.
- [x] 4.5 Verify the new tools are covered by the existing single-approval-chokepoint test (`tests/test_tools_approval.py`) without needing per-tool special-casing; extend it if it currently enumerates tools by name. Confirmed: `request_approval` is tested generically by tool name/args, not enumerated per-tool — no change needed.

## 5. Wiring and verification

- [x] 5.1 Update `vllm_cli/tools/registry.py` imports to include the new `search` and `process` modules.
- [x] 5.2 Run the full test suite (`pytest`) and fix any failures.
