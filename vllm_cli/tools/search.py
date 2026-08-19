import fnmatch
import os
import re
from pathlib import Path
from typing import Optional, Union

from vllm_cli.tools.files import resolve_scoped_path
from vllm_cli.tools.common import ToolError

MAX_MATCHES = 200
MAX_GLOB_RESULTS = 500

DEFAULT_EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "dist", "build"}


def _is_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as fh:
            chunk = fh.read(8192)
    except OSError:
        return True
    return b"\x00" in chunk


def _iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]
        for filename in filenames:
            yield Path(dirpath) / filename


def search_files(
    tools_root: Union[str, Path],
    pattern: str,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
) -> str:
    try:
        root = resolve_scoped_path(tools_root, ".")
    except ToolError as exc:
        return f"Error: {exc}"

    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return f"Error: invalid regular expression '{pattern}': {exc}"

    matches = []
    omitted = 0
    for file_path in sorted(_iter_files(root)):
        rel = file_path.relative_to(root).as_posix()

        if include and not fnmatch.fnmatch(rel, include):
            continue
        if exclude and fnmatch.fnmatch(rel, exclude):
            continue
        if _is_binary(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for lineno, line in enumerate(content.splitlines(), start=1):
            if regex.search(line):
                if len(matches) >= MAX_MATCHES:
                    omitted += 1
                    continue
                matches.append(f"{rel}:{lineno}:{line}")

    if not matches:
        return f"No matches found for pattern '{pattern}'"

    result = "\n".join(matches)
    if omitted:
        result += f"\n... [{omitted} more matches omitted, refine your pattern or filters]"
    return result


def glob_files(tools_root: Union[str, Path], pattern: str) -> str:
    if ".." in Path(pattern).parts:
        return f"Error: pattern '{pattern}' must not contain '..' segments"

    try:
        root = resolve_scoped_path(tools_root, ".")
    except ToolError as exc:
        return f"Error: {exc}"

    try:
        matched = sorted(p for p in root.glob(pattern) if p.is_file())
    except ValueError as exc:
        return f"Error: invalid glob pattern '{pattern}': {exc}"

    if not matched:
        return f"No files matched pattern '{pattern}'"

    rel_paths = [p.relative_to(root).as_posix() for p in matched]
    if len(rel_paths) > MAX_GLOB_RESULTS:
        omitted = len(rel_paths) - MAX_GLOB_RESULTS
        rel_paths = rel_paths[:MAX_GLOB_RESULTS]
        rel_paths.append(f"... [{omitted} more files omitted, refine your pattern]")
    return "\n".join(rel_paths)
