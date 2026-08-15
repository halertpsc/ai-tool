from pathlib import Path
from typing import Any, Dict, List, Union

from vllm_cli.tools.common import MAX_OUTPUT_CHARS, ToolError, truncate_output


def resolve_scoped_path(tools_root: Union[str, Path], path: str) -> Path:
    """Resolve `path` relative to `tools_root`, rejecting anything outside it."""
    root = Path(tools_root).resolve()
    raw = Path(path)
    candidate = (raw if raw.is_absolute() else root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ToolError(
            f"path '{path}' resolves outside the tools working directory '{root}'"
        )
    return candidate


def read_file(tools_root: Union[str, Path], path: str) -> str:
    try:
        resolved = resolve_scoped_path(tools_root, path)
    except ToolError as exc:
        return f"Error: {exc}"
    if not resolved.exists():
        return f"Error: file not found: {path}"
    if not resolved.is_file():
        return f"Error: not a file: {path}"
    try:
        content = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Error: could not read file: {exc}"
    return truncate_output(content, MAX_OUTPUT_CHARS)


def write_file(tools_root: Union[str, Path], path: str, content: str) -> str:
    try:
        resolved = resolve_scoped_path(tools_root, path)
    except ToolError as exc:
        return f"Error: {exc}"
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
    except OSError as exc:
        return f"Error: could not write file: {exc}"
    return f"Wrote {len(content)} characters to {path}"


def edit_file(tools_root: Union[str, Path], path: str, old_text: str, new_text: str) -> str:
    try:
        resolved = resolve_scoped_path(tools_root, path)
    except ToolError as exc:
        return f"Error: {exc}"
    if not resolved.exists():
        return f"Error: file not found: {path}"
    if not resolved.is_file():
        return f"Error: not a file: {path}"
    try:
        content = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        return f"Error: could not read file: {exc}"

    count = content.count(old_text)
    if count == 0:
        return f"Error: old_text not found in {path}"
    if count > 1:
        return (
            f"Error: old_text is ambiguous in {path} "
            f"({count} occurrences); provide more surrounding context"
        )

    new_content = content.replace(old_text, new_text, 1)
    try:
        resolved.write_text(new_content, encoding="utf-8")
    except OSError as exc:
        return f"Error: could not write file: {exc}"
    return f"Edited {path}"


def patch_file(tools_root: Union[str, Path], path: str, edits: List[Dict[str, Any]]) -> str:
    try:
        resolved = resolve_scoped_path(tools_root, path)
    except ToolError as exc:
        return f"Error: {exc}"
    if not resolved.exists():
        return f"Error: file not found: {path}"
    if not resolved.is_file():
        return f"Error: not a file: {path}"
    try:
        content = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        return f"Error: could not read file: {exc}"

    if not edits:
        return f"Error: no edits provided for {path}"

    working = content
    for index, edit in enumerate(edits):
        old_text = edit.get("old_text", "")
        new_text = edit.get("new_text", "")
        count = working.count(old_text)
        if count == 0:
            return f"Error: hunk {index} old_text not found in {path}; no changes were made"
        if count > 1:
            return (
                f"Error: hunk {index} old_text is ambiguous in {path} "
                f"({count} occurrences); no changes were made"
            )
        working = working.replace(old_text, new_text, 1)

    try:
        resolved.write_text(working, encoding="utf-8")
    except OSError as exc:
        return f"Error: could not write file: {exc}"
    return f"Applied {len(edits)} hunk(s) to {path}"


def list_dir(tools_root: Union[str, Path], path: str = ".") -> str:
    try:
        resolved = resolve_scoped_path(tools_root, path)
    except ToolError as exc:
        return f"Error: {exc}"
    if not resolved.exists():
        return f"Error: directory not found: {path}"
    if not resolved.is_dir():
        return f"Error: not a directory: {path}"

    entries = sorted(
        entry.name + "/" if entry.is_dir() else entry.name
        for entry in resolved.iterdir()
    )
    return "\n".join(entries) if entries else "(empty directory)"
