import re
import sys
import time

import vllm_cli.tools.process as process
from vllm_cli.tools.process import (
    MAX_CONCURRENT_PROCESSES,
    list_processes,
    read_process_output,
    send_process_input,
    start_process,
    stop_process,
)


def _extract_id(start_result: str) -> int:
    match = re.match(r"Started process (\d+):", start_result)
    assert match, f"unexpected start_process result: {start_result}"
    return int(match.group(1))


def _status_line(tools_root, process_id) -> str:
    prefix = f"{process_id}: "
    for line in list_processes(tools_root).splitlines():
        if line.startswith(prefix):
            return line
    return ""


def _wait_until_exited(tools_root, process_id, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if "exited" in _status_line(tools_root, process_id):
            return
        time.sleep(0.05)
    raise AssertionError(f"process {process_id} did not exit within {timeout}s")


def test_process_lifecycle(tmp_path):
    process_id = _extract_id(
        start_process(tmp_path, [sys.executable, "-c", "print('hello'); print('world')"])
    )
    try:
        _wait_until_exited(tmp_path, process_id)
        listing = list_processes(tmp_path)
        assert f"{process_id}:" in listing
        assert "exited (0)" in listing

        output = read_process_output(tmp_path, process_id)
        assert "hello" in output
        assert "world" in output
    finally:
        stop_process(tmp_path, process_id)


def test_read_process_output_drains_between_reads(tmp_path):
    process_id = _extract_id(
        start_process(tmp_path, [sys.executable, "-c", "print('first')"])
    )
    try:
        _wait_until_exited(tmp_path, process_id)
        first_read = read_process_output(tmp_path, process_id)
        assert "first" in first_read

        second_read = read_process_output(tmp_path, process_id)
        assert "first" not in second_read
        assert "no new output" in second_read
    finally:
        stop_process(tmp_path, process_id)


def test_send_process_input(tmp_path):
    script = (
        "import sys; "
        "line = sys.stdin.readline(); "
        "print('got:' + line.strip())"
    )
    process_id = _extract_id(start_process(tmp_path, [sys.executable, "-c", script]))
    try:
        result = send_process_input(tmp_path, process_id, "hello\n")
        assert "Wrote" in result
        _wait_until_exited(tmp_path, process_id)
        output = read_process_output(tmp_path, process_id)
        assert "got:hello" in output
    finally:
        stop_process(tmp_path, process_id)


def test_send_process_input_to_exited_process_errors(tmp_path):
    process_id = _extract_id(start_process(tmp_path, [sys.executable, "-c", "pass"]))
    _wait_until_exited(tmp_path, process_id)
    result = send_process_input(tmp_path, process_id, "hello\n")
    assert "Error" in result
    assert "already exited" in result


def test_stop_process_graceful(tmp_path):
    process_id = _extract_id(
        start_process(tmp_path, [sys.executable, "-c", "import time; time.sleep(30)"])
    )
    result = stop_process(tmp_path, process_id)
    assert "Stopped process" in result


def test_stop_already_exited_process_is_not_an_error(tmp_path):
    process_id = _extract_id(start_process(tmp_path, [sys.executable, "-c", "pass"]))
    _wait_until_exited(tmp_path, process_id)
    result = stop_process(tmp_path, process_id)
    assert "Error" not in result
    assert "already exited" in result


def test_unknown_process_id_errors(tmp_path):
    assert "Error" in read_process_output(tmp_path, 999999)
    assert "Error" in send_process_input(tmp_path, 999999, "x")
    assert "Error" in stop_process(tmp_path, 999999)


def test_concurrency_cap_enforced(tmp_path):
    started = []
    try:
        for _ in range(MAX_CONCURRENT_PROCESSES):
            started.append(
                _extract_id(
                    start_process(
                        tmp_path, [sys.executable, "-c", "import time; time.sleep(30)"]
                    )
                )
            )
        result = start_process(tmp_path, [sys.executable, "-c", "print('one too many')"])
        assert "Error" in result
        assert "concurrency cap" in result
    finally:
        for process_id in started:
            stop_process(tmp_path, process_id)


def test_output_buffer_bound_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(process, "MAX_BUFFER_CHARS", 50)
    script = "for i in range(200): print('x' * 20)"
    process_id = _extract_id(start_process(tmp_path, [sys.executable, "-c", script]))
    try:
        _wait_until_exited(tmp_path, process_id)
        output = read_process_output(tmp_path, process_id)
        assert "characters of older output were dropped" in output
    finally:
        stop_process(tmp_path, process_id)
