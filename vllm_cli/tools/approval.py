import json
import sys
from typing import Any, Dict

import click


def request_approval(tool_name: str, arguments: Dict[str, Any]) -> bool:
    """Prompt the user to approve a single tool call. Fails closed (denies) if
    the session is not interactive, and never caches a prior answer."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        click.echo(
            f"[tool call denied: no interactive terminal available] {tool_name}",
            err=True,
        )
        return False

    click.echo("")
    click.echo(f"Tool call requested: {tool_name}")
    click.echo(json.dumps(arguments, indent=2, default=str))
    return click.confirm("Approve this tool call?", default=False)
