import atexit
import shlex
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

MAX_CONCURRENT_PROCESSES = 5
MAX_BUFFER_CHARS = 8000
STOP_GRACE_PERIOD = 3.0


@dataclass
class ProcessHandle:
    process_id: int
    command: str
    popen: subprocess.Popen
    buffer: List[str] = field(default_factory=list)
    dropped_chars: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)


_REGISTRY: Dict[int, ProcessHandle] = {}
_NEXT_ID = 1
_REGISTRY_LOCK = threading.Lock()


def _command_to_str(command: Union[str, List[str]]) -> str:
    return command if isinstance(command, str) else " ".join(command)


def _reader_thread(handle: ProcessHandle, stream, tag: str) -> None:
    for line in iter(stream.readline, ""):
        chunk = f"[{tag}] {line}" if tag else line
        with handle.lock:
            handle.buffer.append(chunk)
            joined_len = sum(len(c) for c in handle.buffer)
            while joined_len > MAX_BUFFER_CHARS and len(handle.buffer) > 1:
                dropped = handle.buffer.pop(0)
                handle.dropped_chars += len(dropped)
                joined_len -= len(dropped)
    stream.close()


def start_process(
    tools_root: Union[str, Path],
    command: Union[str, List[str]],
    shell: bool = False,
) -> str:
    cwd = Path(tools_root).resolve()

    with _REGISTRY_LOCK:
        live = sum(1 for h in _REGISTRY.values() if h.popen.poll() is None)
        if live >= MAX_CONCURRENT_PROCESSES:
            return (
                f"Error: concurrency cap reached ({MAX_CONCURRENT_PROCESSES} live "
                "background processes); stop one before starting another"
            )

        if isinstance(command, str):
            argv: Union[str, List[str]] = command if shell else shlex.split(command)
        else:
            argv = list(command)

        try:
            popen = subprocess.Popen(
                argv,
                shell=shell,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            return f"Error: failed to start process: {exc}"

        global _NEXT_ID
        process_id = _NEXT_ID
        _NEXT_ID += 1

        handle = ProcessHandle(process_id=process_id, command=_command_to_str(command), popen=popen)
        _REGISTRY[process_id] = handle

    threading.Thread(target=_reader_thread, args=(handle, popen.stdout, ""), daemon=True).start()
    threading.Thread(target=_reader_thread, args=(handle, popen.stderr, "stderr"), daemon=True).start()

    return f"Started process {process_id}: {handle.command}"


def list_processes(tools_root: Union[str, Path]) -> str:
    if not _REGISTRY:
        return "No tracked background processes"

    lines = []
    for handle in sorted(_REGISTRY.values(), key=lambda h: h.process_id):
        exit_code = handle.popen.poll()
        status = "running" if exit_code is None else f"exited ({exit_code})"
        lines.append(f"{handle.process_id}: {handle.command} [{status}]")
    return "\n".join(lines)


def _get_handle(process_id: int) -> Optional[ProcessHandle]:
    return _REGISTRY.get(process_id)


def read_process_output(tools_root: Union[str, Path], process_id: int) -> str:
    handle = _get_handle(process_id)
    if handle is None:
        return f"Error: unknown process id {process_id}"

    with handle.lock:
        output = "".join(handle.buffer)
        dropped = handle.dropped_chars
        handle.buffer.clear()
        handle.dropped_chars = 0

    exit_code = handle.popen.poll()
    status = "running" if exit_code is None else f"exited ({exit_code})"
    parts = [f"Status: {status}"]
    if dropped:
        parts.append(f"[{dropped} characters of older output were dropped]")
    parts.append(output if output else "(no new output)")
    return "\n".join(parts)


def send_process_input(tools_root: Union[str, Path], process_id: int, text: str) -> str:
    handle = _get_handle(process_id)
    if handle is None:
        return f"Error: unknown process id {process_id}"
    if handle.popen.poll() is not None:
        return f"Error: process {process_id} has already exited"
    try:
        handle.popen.stdin.write(text)
        handle.popen.stdin.flush()
    except OSError as exc:
        return f"Error: failed to write to process {process_id}: {exc}"
    return f"Wrote {len(text)} characters to process {process_id} stdin"


def stop_process(tools_root: Union[str, Path], process_id: int) -> str:
    handle = _get_handle(process_id)
    if handle is None:
        return f"Error: unknown process id {process_id}"

    if handle.popen.poll() is not None:
        return f"Process {process_id} had already exited (code {handle.popen.returncode})"

    handle.popen.terminate()
    try:
        handle.popen.wait(timeout=STOP_GRACE_PERIOD)
        return f"Stopped process {process_id} (code {handle.popen.returncode})"
    except subprocess.TimeoutExpired:
        handle.popen.kill()
        handle.popen.wait()
        return f"Process {process_id} did not exit gracefully; force-killed (code {handle.popen.returncode})"


def _cleanup_on_exit() -> None:
    for handle in list(_REGISTRY.values()):
        if handle.popen.poll() is None:
            try:
                handle.popen.terminate()
                handle.popen.wait(timeout=STOP_GRACE_PERIOD)
            except Exception:
                try:
                    handle.popen.kill()
                except Exception:
                    pass


atexit.register(_cleanup_on_exit)
