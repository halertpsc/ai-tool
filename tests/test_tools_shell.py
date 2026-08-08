import sys

from vllm_cli.tools.shell import run_command


def test_run_command_success(tmp_path):
    result = run_command(tmp_path, [sys.executable, "-c", "print('hello')"])
    assert "Exit code: 0" in result
    assert "hello" in result


def test_run_command_nonzero_exit(tmp_path):
    result = run_command(tmp_path, [sys.executable, "-c", "import sys; sys.exit(3)"])
    assert "Exit code: 3" in result


def test_run_command_captures_stderr(tmp_path):
    result = run_command(
        tmp_path, [sys.executable, "-c", "import sys; sys.stderr.write('oops')"]
    )
    assert "oops" in result


def test_run_command_timeout(tmp_path):
    result = run_command(
        tmp_path, [sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2
    )
    assert "Error" in result
    assert "timed out" in result


def test_run_command_cwd_scoped(tmp_path):
    (tmp_path / "marker.txt").write_text("x", encoding="utf-8")
    result = run_command(tmp_path, [sys.executable, "-c", "import os; print(os.getcwd())"])
    assert str(tmp_path.resolve()) in result


def test_run_command_string_uses_shlex(tmp_path):
    result = run_command(tmp_path, f'"{sys.executable}" -c "print(1)"')
    assert "Exit code: 0" in result
    assert "1" in result
