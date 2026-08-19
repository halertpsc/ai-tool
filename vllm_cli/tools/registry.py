from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from vllm_cli.tools import files, process, search, shell, web


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[..., str]

    def to_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


BUILTIN_TOOLS: List[Tool] = [
    Tool(
        name="read_file",
        description="Read the text content of a file within the tools working directory.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path relative to the tools working directory.",
                },
            },
            "required": ["path"],
        },
        handler=files.read_file,
    ),
    Tool(
        name="write_file",
        description=(
            "Create or overwrite a file within the tools working directory "
            "with the given content."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path relative to the tools working directory.",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file.",
                },
            },
            "required": ["path", "content"],
        },
        handler=files.write_file,
    ),
    Tool(
        name="edit_file",
        description="Replace an exact, unique text snippet within an existing file.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path relative to the tools working directory.",
                },
                "old_text": {
                    "type": "string",
                    "description": "Exact text to find; must be unique in the file.",
                },
                "new_text": {
                    "type": "string",
                    "description": "Replacement text.",
                },
            },
            "required": ["path", "old_text", "new_text"],
        },
        handler=files.edit_file,
    ),
    Tool(
        name="patch_file",
        description=(
            "Apply multiple exact-match text replacements to an existing file in one call. "
            "Each edit's old_text must be unique in the file at the point it is applied. "
            "All edits succeed and are written together, or none are."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path relative to the tools working directory.",
                },
                "edits": {
                    "type": "array",
                    "description": "Ordered list of hunks to apply.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "old_text": {
                                "type": "string",
                                "description": "Exact text to find; must be unique in the file at this point.",
                            },
                            "new_text": {
                                "type": "string",
                                "description": "Replacement text.",
                            },
                        },
                        "required": ["old_text", "new_text"],
                    },
                },
            },
            "required": ["path", "edits"],
        },
        handler=files.patch_file,
    ),
    Tool(
        name="list_dir",
        description="List the direct entries of a directory within the tools working directory.",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path relative to the tools working directory. Defaults to '.'.",
                },
            },
            "required": [],
        },
        handler=files.list_dir,
    ),
    Tool(
        name="search_files",
        description=(
            "Search file contents under the tools working directory for a regular-expression "
            "pattern, returning matching lines as path:line:content."
        ),
        parameters={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression to search for.",
                },
                "include": {
                    "type": "string",
                    "description": "Optional glob filter; only files matching this are searched.",
                },
                "exclude": {
                    "type": "string",
                    "description": "Optional glob filter; files matching this are skipped.",
                },
            },
            "required": ["pattern"],
        },
        handler=search.search_files,
    ),
    Tool(
        name="glob_files",
        description="Find files under the tools working directory matching a glob pattern (e.g. '**/*.py').",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match file paths against.",
                },
            },
            "required": ["pattern"],
        },
        handler=search.glob_files,
    ),
    Tool(
        name="fetch_url",
        description="Fetch the content of an http(s) URL via HTTP GET.",
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The http(s) URL to fetch.",
                },
            },
            "required": ["url"],
        },
        handler=web.fetch_url,
    ),
    Tool(
        name="run_command",
        description="Run a CLI command as a subprocess within the tools working directory.",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "string"},
                    ],
                    "description": (
                        "Command to run. Prefer an argv array; a plain string is "
                        "also accepted and split with shlex unless shell=true."
                    ),
                },
                "shell": {
                    "type": "boolean",
                    "description": "Run via the system shell. Default false.",
                },
            },
            "required": ["command"],
        },
        handler=shell.run_command,
    ),
    Tool(
        name="start_process",
        description=(
            "Launch a subprocess that keeps running in the background across multiple tool "
            "calls (e.g. a dev server). Returns a process ID for use with list_processes, "
            "read_process_output, send_process_input, and stop_process."
        ),
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "string"},
                    ],
                    "description": (
                        "Command to run. Prefer an argv array; a plain string is "
                        "also accepted and split with shlex unless shell=true."
                    ),
                },
                "shell": {
                    "type": "boolean",
                    "description": "Run via the system shell. Default false.",
                },
            },
            "required": ["command"],
        },
        handler=process.start_process,
    ),
    Tool(
        name="list_processes",
        description="List all background processes tracked in this session, with their status.",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=process.list_processes,
    ),
    Tool(
        name="read_process_output",
        description=(
            "Read a background process's stdout/stderr output accumulated since the last "
            "read, without blocking. Also reports whether the process is still running."
        ),
        parameters={
            "type": "object",
            "properties": {
                "process_id": {
                    "type": "integer",
                    "description": "ID returned by start_process.",
                },
            },
            "required": ["process_id"],
        },
        handler=process.read_process_output,
    ),
    Tool(
        name="send_process_input",
        description="Write text to a running background process's stdin.",
        parameters={
            "type": "object",
            "properties": {
                "process_id": {
                    "type": "integer",
                    "description": "ID returned by start_process.",
                },
                "text": {
                    "type": "string",
                    "description": "Text to write to the process's stdin.",
                },
            },
            "required": ["process_id", "text"],
        },
        handler=process.send_process_input,
    ),
    Tool(
        name="stop_process",
        description=(
            "Stop a background process, escalating to a forceful kill if it does not exit "
            "gracefully within a short grace period."
        ),
        parameters={
            "type": "object",
            "properties": {
                "process_id": {
                    "type": "integer",
                    "description": "ID returned by start_process.",
                },
            },
            "required": ["process_id"],
        },
        handler=process.stop_process,
    ),
]

_BY_NAME = {tool.name: tool for tool in BUILTIN_TOOLS}


def get_tool(name: str) -> Tool:
    try:
        return _BY_NAME[name]
    except KeyError:
        raise KeyError(f"Unknown tool: {name}")


def tool_schemas() -> List[Dict[str, Any]]:
    return [tool.to_schema() for tool in BUILTIN_TOOLS]
