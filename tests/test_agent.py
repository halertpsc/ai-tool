from unittest.mock import MagicMock, patch

from vllm_cli.agent import run_agent_turn
from vllm_cli.tools.registry import get_tool


def _tool_call_response(call_id="call_1", name="read_file", arguments='{"path": "a.txt"}'):
    return {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {"name": name, "arguments": arguments},
                        }
                    ],
                }
            }
        ]
    }


def _final_response(content="Done."):
    return {"choices": [{"message": {"content": content, "tool_calls": []}}]}


def test_agent_turn_approved_tool_call_executes_and_loops(tmp_path):
    (tmp_path / "a.txt").write_text("hi", encoding="utf-8")
    client = MagicMock()
    client.chat.side_effect = [_tool_call_response(), _final_response("The file says hi.")]
    history = [{"role": "user", "content": "read a.txt"}]

    with patch("vllm_cli.agent.request_approval", return_value=True):
        reply = run_agent_turn(client, history, str(tmp_path), use_stream=False, params={})

    assert reply == "The file says hi."
    assert client.chat.call_count == 2
    tool_messages = [m for m in history if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    assert tool_messages[0]["content"] == "hi"
    assert tool_messages[0]["tool_call_id"] == "call_1"


def test_agent_turn_denied_tool_call_not_executed(tmp_path):
    client = MagicMock()
    client.chat.side_effect = [_tool_call_response(), _final_response("Okay, skipping.")]
    history = [{"role": "user", "content": "read a.txt"}]

    with patch("vllm_cli.agent.request_approval", return_value=False), \
         patch.object(get_tool("read_file"), "handler") as mock_handler:
        reply = run_agent_turn(client, history, str(tmp_path), use_stream=False, params={})

    assert reply == "Okay, skipping."
    mock_handler.assert_not_called()
    tool_messages = [m for m in history if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    assert "denied" in tool_messages[0]["content"].lower()


def test_agent_turn_no_tool_call_returns_content_directly(tmp_path):
    client = MagicMock()
    client.chat.return_value = _final_response("Hi there.")
    history = [{"role": "user", "content": "hello"}]

    with patch("vllm_cli.agent.request_approval") as mock_approval:
        reply = run_agent_turn(client, history, str(tmp_path), use_stream=False, params={})

    assert reply == "Hi there."
    mock_approval.assert_not_called()
    assert client.chat.call_count == 1


def test_agent_turn_malformed_arguments_reported_without_crash(tmp_path):
    client = MagicMock()
    client.chat.side_effect = [
        _tool_call_response(arguments="not-json"),
        _final_response("Got it."),
    ]
    history = [{"role": "user", "content": "do something"}]

    with patch("vllm_cli.agent.request_approval") as mock_approval:
        reply = run_agent_turn(client, history, str(tmp_path), use_stream=False, params={})

    mock_approval.assert_not_called()
    tool_messages = [m for m in history if m.get("role") == "tool"]
    assert "malformed" in tool_messages[0]["content"].lower()
    assert reply == "Got it."


def test_agent_turn_unknown_tool_reported_without_crash(tmp_path):
    client = MagicMock()
    client.chat.side_effect = [
        _tool_call_response(name="does_not_exist", arguments="{}"),
        _final_response("Got it."),
    ]
    history = [{"role": "user", "content": "do something"}]

    with patch("vllm_cli.agent.request_approval") as mock_approval:
        reply = run_agent_turn(client, history, str(tmp_path), use_stream=False, params={})

    mock_approval.assert_not_called()
    tool_messages = [m for m in history if m.get("role") == "tool"]
    assert "unknown tool" in tool_messages[0]["content"].lower()
    assert reply == "Got it."
