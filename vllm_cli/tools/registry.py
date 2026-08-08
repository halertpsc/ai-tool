from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from vllm_cli.tools import files, shell, web


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
]

_BY_NAME = {tool.name: tool for tool in BUILTIN_TOOLS}


def get_tool(name: str) -> Tool:
    try:
        return _BY_NAME[name]
    except KeyError:
        raise KeyError(f"Unknown tool: {name}")


def tool_schemas() -> List[Dict[str, Any]]:
    return [tool.to_schema() for tool in BUILTIN_TOOLS]
