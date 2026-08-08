from unittest.mock import patch

from vllm_cli.tools.approval import request_approval


def test_approval_granted():
    with patch("vllm_cli.tools.approval.sys.stdin.isatty", return_value=True), \
         patch("vllm_cli.tools.approval.sys.stdout.isatty", return_value=True), \
         patch("click.confirm", return_value=True) as mock_confirm:
        assert request_approval("read_file", {"path": "a.txt"}) is True
    mock_confirm.assert_called_once()


def test_approval_denied():
    with patch("vllm_cli.tools.approval.sys.stdin.isatty", return_value=True), \
         patch("vllm_cli.tools.approval.sys.stdout.isatty", return_value=True), \
         patch("click.confirm", return_value=False):
        assert request_approval("run_command", {"command": ["rm", "-rf", "/"]}) is False


def test_approval_fails_closed_when_no_tty():
    with patch("vllm_cli.tools.approval.sys.stdin.isatty", return_value=False), \
         patch("vllm_cli.tools.approval.sys.stdout.isatty", return_value=True), \
         patch("click.confirm") as mock_confirm:
        assert request_approval("write_file", {"path": "a.txt", "content": "x"}) is False
    mock_confirm.assert_not_called()


def test_approval_fails_closed_when_stdout_not_tty():
    with patch("vllm_cli.tools.approval.sys.stdin.isatty", return_value=True), \
         patch("vllm_cli.tools.approval.sys.stdout.isatty", return_value=False), \
         patch("click.confirm") as mock_confirm:
        assert request_approval("write_file", {"path": "a.txt"}) is False
    mock_confirm.assert_not_called()
