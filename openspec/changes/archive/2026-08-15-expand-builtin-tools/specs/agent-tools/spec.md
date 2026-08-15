## ADDED Requirements

### Requirement: Search files tool
The system SHALL provide a `search_files` tool that searches the text content of files under the tools working directory for a regular-expression pattern and returns matching lines with their file path and line number.

#### Scenario: Matches returned
- **WHEN** the model calls `search_files` with a valid regex pattern and the call is approved
- **THEN** the tool returns each match as the file's relative path, line number, and matching line content

#### Scenario: No matches found
- **WHEN** the pattern matches no content under the tools working directory
- **THEN** the tool returns a result stating no matches were found, not an error

#### Scenario: Include/exclude filters applied
- **WHEN** the model supplies an include and/or exclude glob filter alongside the pattern
- **THEN** only files matching the include filter (if given) and not matching the exclude filter (if given) are searched

#### Scenario: Default noise directories skipped
- **WHEN** `search_files` walks the tools working directory
- **THEN** common non-source directories (`.git`, `__pycache__`, `node_modules`, `.venv`, `dist`, `build`) are skipped by default without requiring an explicit exclude filter

#### Scenario: Binary files skipped
- **WHEN** a file under the search path is detected as binary content
- **THEN** the tool skips that file rather than raising an error or returning garbled matches

#### Scenario: Match count capped
- **WHEN** the number of matches exceeds a fixed cap
- **THEN** the tool returns matches up to the cap and states that additional matches were omitted

#### Scenario: Invalid regex rejected
- **WHEN** the model calls `search_files` with a pattern that is not a valid regular expression
- **THEN** the tool returns an error result without performing a search

### Requirement: Glob files tool
The system SHALL provide a `glob_files` tool that returns the relative paths of files under the tools working directory matching a glob pattern (e.g. `**/*.py`).

#### Scenario: Matching files returned
- **WHEN** the model calls `glob_files` with a pattern and the call is approved
- **THEN** the tool returns the relative paths of all files under the tools working directory matching that pattern

#### Scenario: No matches found
- **WHEN** the pattern matches no files
- **THEN** the tool returns a result stating no files matched, not an error

#### Scenario: Path traversal in pattern rejected
- **WHEN** the model calls `glob_files` with a pattern containing `..` segments
- **THEN** the tool returns an error result without performing a filesystem search

### Requirement: Patch file tool
The system SHALL provide a `patch_file` tool that applies an ordered list of exact-match `old_text`/`new_text` hunks to a single existing file, writing the file only if every hunk applies cleanly.

#### Scenario: All hunks applied
- **WHEN** the model calls `patch_file` with a path and a list of hunks, each `old_text` unique in the content at the point it is applied, and the call is approved
- **THEN** the tool applies all hunks in order, writes the result once, and returns a confirmation as the tool result

#### Scenario: A failing hunk aborts the whole patch
- **WHEN** any hunk's `old_text` is not found, or matches more than once, in the content at the point it would be applied
- **THEN** the tool makes no change to the file and returns an error result identifying the failing hunk's index and reason

## MODIFIED Requirements

### Requirement: Filesystem tools scoped to a working directory
File and directory tools (`read_file`, `write_file`, `edit_file`, `list_dir`, `search_files`, `glob_files`, `patch_file`) and `run_command` SHALL resolve relative paths against a configured tools working directory (defaulting to the directory `vllm-cli` was launched from) and SHALL reject any resolved path that falls outside that directory.

#### Scenario: Path traversal rejected
- **WHEN** the model calls a filesystem tool with a path containing `..` segments that resolve outside the tools working directory
- **THEN** the tool returns an error result and performs no filesystem operation

#### Scenario: Working directory configurable
- **WHEN** the user starts a chat session with `--tools-root <dir>`
- **THEN** filesystem and command tools resolve relative paths against `<dir>` instead of the default working directory

### Requirement: Tool output truncation
Tool results returned to the model SHALL be truncated to a fixed maximum character length, with an explicit truncation notice appended when truncation occurs.

#### Scenario: Oversized output truncated
- **WHEN** a tool's raw output (file content, command output, fetched URL body, or `search_files`/`glob_files` results) exceeds the configured maximum length
- **THEN** the tool result sent back to the model is cut to that maximum and ends with a notice indicating it was truncated
