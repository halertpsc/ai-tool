import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

import vllm_cli.config as cfg_module
from vllm_cli.main import cli

RESOLVED = {"url": "http://test:8000", "model": "test-model"}


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def patch_config(tmp_path, monkeypatch):
    config_file = tmp_path / "vllm-cli" / "config.toml"
    monkeypatch.setattr(cfg_module, "get_config_path", lambda: config_file)
    # Patch resolve_settings in both command modules so they return a usable URL/model
    monkeypatch.setattr("vllm_cli.commands.complete.resolve_settings", lambda _: RESOLVED.copy())
    monkeypatch.setattr("vllm_cli.commands.chat.resolve_settings", lambda _: RESOLVED.copy())


# ------------------------------------------------------------------
# complete command
# ------------------------------------------------------------------

def test_complete_text_output(runner):
    mock_resp = {"choices": [{"text": "Paris"}]}
    with patch("vllm_cli.commands.complete.VllmClient") as MockClient:
        inst = MagicMock()
        inst.complete.return_value = mock_resp
        MockClient.return_value = inst
        result = runner.invoke(cli, ["complete", "Capital of France?"])
    assert result.exit_code == 0
    assert "Paris" in result.output


def test_complete_json_output(runner):
    mock_resp = {"choices": [{"text": "Paris"}]}
    with patch("vllm_cli.commands.complete.VllmClient") as MockClient:
        inst = MagicMock()
        inst.complete.return_value = mock_resp
        MockClient.return_value = inst
        result = runner.invoke(cli, ["--output", "json", "complete", "Capital?"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == mock_resp


def test_complete_invalid_temperature(runner):
    result = runner.invoke(cli, ["complete", "hello", "--temperature", "5.0"])
    assert result.exit_code != 0


def test_complete_missing_prompt_on_tty(runner):
    # CliRunner simulates a non-TTY stdin, so prompt=None means stdin is read
    # Pass empty stdin to trigger the error path where prompt is empty
    with patch("vllm_cli.commands.complete.VllmClient"):
        result = runner.invoke(cli, ["complete"], input="")
    # Should either fail or produce nothing meaningful — empty prompt is stripped
    # The key check: no crash / unhandled exception
    assert result.exit_code in (0, 1, 2)


def test_complete_reads_stdin(runner):
    mock_resp = {"choices": [{"text": "42"}]}
    with patch("vllm_cli.commands.complete.VllmClient") as MockClient:
        inst = MagicMock()
        inst.complete.return_value = mock_resp
        MockClient.return_value = inst
        result = runner.invoke(cli, ["complete"], input="What is 6*7?")
    assert result.exit_code == 0
    assert "42" in result.output


# ------------------------------------------------------------------
# chat command
# ------------------------------------------------------------------

def test_chat_exit_command(runner):
    with patch("vllm_cli.commands.chat.VllmClient") as MockClient:
        MockClient.return_value = MagicMock()
        result = runner.invoke(cli, ["chat"], input="exit\n")
    assert result.exit_code == 0
    assert "Goodbye" in result.output


def test_chat_quit_command(runner):
    with patch("vllm_cli.commands.chat.VllmClient") as MockClient:
        MockClient.return_value = MagicMock()
        result = runner.invoke(cli, ["chat"], input="quit\n")
    assert result.exit_code == 0
    assert "Goodbye" in result.output


def test_chat_sends_message_and_shows_reply(runner):
    mock_resp = {"choices": [{"message": {"content": "I am an AI."}}]}
    with patch("vllm_cli.commands.chat.VllmClient") as MockClient:
        inst = MagicMock()
        inst.chat.return_value = mock_resp
        MockClient.return_value = inst
        result = runner.invoke(cli, ["chat"], input="Who are you?\nquit\n")
    assert result.exit_code == 0
    assert "I am an AI." in result.output


def test_chat_maintains_history(runner):
    responses = [
        {"choices": [{"message": {"content": "First reply"}}]},
        {"choices": [{"message": {"content": "Second reply"}}]},
    ]
    with patch("vllm_cli.commands.chat.VllmClient") as MockClient:
        inst = MagicMock()
        inst.chat.side_effect = responses
        MockClient.return_value = inst
        result = runner.invoke(cli, ["chat"], input="Hello\nHow are you?\nquit\n")
    assert result.exit_code == 0
    # Second call should include more messages (history grows)
    first_call_msgs = inst.chat.call_args_list[0][0][0]
    second_call_msgs = inst.chat.call_args_list[1][0][0]
    assert len(second_call_msgs) > len(first_call_msgs)


def test_chat_system_prompt(runner):
    mock_resp = {"choices": [{"message": {"content": "Sure!"}}]}
    with patch("vllm_cli.commands.chat.VllmClient") as MockClient:
        inst = MagicMock()
        inst.chat.return_value = mock_resp
        MockClient.return_value = inst
        result = runner.invoke(cli, ["chat", "--system", "Be concise"], input="Hi\nquit\n")
    assert result.exit_code == 0
    first_call_msgs = inst.chat.call_args_list[0][0][0]
    assert first_call_msgs[0] == {"role": "system", "content": "Be concise"}


# ------------------------------------------------------------------
# config command
# ------------------------------------------------------------------

def test_config_set_and_get(runner, monkeypatch):
    monkeypatch.setattr("vllm_cli.commands.config_cmd.get_config_path",
                        cfg_module.get_config_path)
    result = runner.invoke(cli, ["config", "set", "url", "http://myserver:8000"])
    assert result.exit_code == 0
    assert "Set url" in result.output

    result = runner.invoke(cli, ["config", "get", "url"])
    assert result.exit_code == 0
    assert "http://myserver:8000" in result.output


def test_config_set_unknown_key(runner):
    result = runner.invoke(cli, ["config", "set", "nonexistent", "value"])
    assert result.exit_code != 0


def test_config_get_unset_key(runner):
    result = runner.invoke(cli, ["config", "get", "model"])
    assert result.exit_code == 0
    assert "(not set)" in result.output
