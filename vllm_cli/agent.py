import json
import sys
from typing import Any, Dict, List

import click

from vllm_cli.client import VllmClient
from vllm_cli.sse import collect_stream
from vllm_cli.tools.approval import request_approval
from vllm_cli.tools.registry import get_tool, tool_schemas

MAX_TOOL_ROUNDS = 25


def run_agent_turn(
    client: VllmClient,
    history: List[dict],
    tools_root: str,
    use_stream: bool,
    params: Dict[str, Any],
) -> str:
    """Drive one user turn through the tool-call loop: send the request with tool
    schemas, and for each tool call the model requests, gate it through approval,
    execute if approved, append the tool result, and resend — until the model
    replies with no further tool calls. Prints "Assistant: " once content is
    available. Returns the final assistant reply text."""
    content = ""
    for _ in range(MAX_TOOL_ROUNDS):
        if use_stream:
            content, tool_calls = _stream_round(client, history, params)
        else:
            content, tool_calls = _sync_round(client, history, params)

        if not tool_calls:
            return content

        history.append(_assistant_tool_call_message(content, tool_calls))
        for tool_call in tool_calls:
            history.append(_execute_tool_call(tool_call, tools_root))

    return content


def _sync_round(client: VllmClient, history: List[dict], params: Dict[str, Any]):
    response = client.chat(list(history), tools=tool_schemas(), **params)
    message = response["choices"][0]["message"]
    content = message.get("content") or ""
    tool_calls = [
        {
            "id": tc.get("id"),
            "name": (tc.get("function") or {}).get("name"),
            "arguments": (tc.get("function") or {}).get("arguments", ""),
        }
        for tc in (message.get("tool_calls") or [])
    ]
    if content:
        click.echo("Assistant: ", nl=False)
        click.echo(content)
    return content, tool_calls


def _stream_round(client: VllmClient, history: List[dict], params: Dict[str, Any]):
    state = {"label_printed": False}

    def on_content(text: str) -> None:
        if not state["label_printed"]:
            click.echo("Assistant: ", nl=False)
            state["label_printed"] = True
        sys.stdout.write(text)
        sys.stdout.flush()

    result = collect_stream(
        client.chat_stream_events(list(history), tools=tool_schemas(), **params),
        on_content=on_content,
    )
    if state["label_printed"]:
        sys.stdout.write("\n")
        sys.stdout.flush()
    return result["content"], result["tool_calls"]


def _assistant_tool_call_message(content: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "role": "assistant",
        "content": content or None,
        "tool_calls": [
            {
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]},
            }
            for tc in tool_calls
        ],
    }


def _execute_tool_call(tool_call: Dict[str, Any], tools_root: str) -> Dict[str, Any]:
    tool_call_id = tool_call.get("id") or ""
    name = tool_call.get("name") or ""
    raw_arguments = tool_call.get("arguments") or "{}"

    try:
        arguments = json.loads(raw_arguments) if raw_arguments.strip() else {}
    except json.JSONDecodeError:
        return _tool_result(
            tool_call_id, f"Error: malformed arguments for tool '{name}': {raw_arguments!r}"
        )

    try:
        tool = get_tool(name)
    except KeyError:
        return _tool_result(tool_call_id, f"Error: unknown tool '{name}'")

    # Single chokepoint: no tool handler may run without explicit approval here.
    if not request_approval(name, arguments):
        return _tool_result(tool_call_id, "User denied this tool call.")

    try:
        output = tool.handler(tools_root, **arguments)
    except TypeError as exc:
        output = f"Error: invalid arguments for tool '{name}': {exc}"
    except Exception as exc:  # tool handlers must not crash the session
        output = f"Error: tool '{name}' failed: {exc}"

    return _tool_result(tool_call_id, output)


def _tool_result(tool_call_id: str, content: str) -> Dict[str, Any]:
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}
