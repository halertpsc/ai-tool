import shlex
import subprocess
from pathlib import Path
from typing import List, Union

from vllm_cli.tools.common import MAX_OUTPUT_CHARS, truncate_output

DEFAULT_TIMEOUT = 30.0


def run_command(
    tools_root: Union[str, Path],
    command: Union[str, List[str]],
    shell: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    cwd = Path(tools_root).resolve()

    if isinstance(command, str):
        argv: Union[str, List[str]] = command if shell else shlex.split(command)
    else:
        argv = list(command)

    try:
        result = subprocess.run(
            argv,
            shell=shell,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    except OSError as exc:
        return f"Error: failed to execute command: {exc}"

    output = (
        f"Exit code: {result.returncode}\n\n"
        f"stdout:\n{result.stdout}\n\n"
        f"stderr:\n{result.stderr}"
    )
    return truncate_output(output, MAX_OUTPUT_CHARS)
