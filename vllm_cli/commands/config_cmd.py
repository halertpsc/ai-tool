import sys

import click
from rich.console import Console
from rich.table import Table

from vllm_cli.config import KEY_TYPES, VALID_KEYS, config_read, config_write, get_config_path

console = Console()


@click.group()
def config_group() -> None:
    """Manage vllm-cli configuration."""


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    if key not in VALID_KEYS:
        valid = ", ".join(sorted(VALID_KEYS))
        raise click.UsageError(f"Unknown key '{key}'. Valid keys: {valid}")

    target_type = KEY_TYPES.get(key, str)
    try:
        if target_type is int:
            typed_value: object = int(value)
        elif target_type is float:
            typed_value = float(value)
        elif target_type is bool:
            lowered = value.strip().lower()
            if lowered in ("true", "1", "yes", "on"):
                typed_value = True
            elif lowered in ("false", "0", "no", "off"):
                typed_value = False
            else:
                raise ValueError(value)
        else:
            typed_value = value
    except ValueError:
        raise click.UsageError(f"Invalid value for '{key}': expected {target_type.__name__}")

    config_write({key: typed_value})
    click.echo(f"Set {key} = {typed_value}")


@config_group.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value."""
    if key not in VALID_KEYS:
        valid = ", ".join(sorted(VALID_KEYS))
        raise click.UsageError(f"Unknown key '{key}'. Valid keys: {valid}")
    data = config_read()
    val = data.get(key)
    click.echo("(not set)" if val is None else str(val))


@config_group.command("show")
def config_show() -> None:
    """Show all configuration values."""
    data = config_read()
    path = get_config_path()

    if sys.stdout.isatty():
        table = Table(title=f"vllm-cli config  ({path})")
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for key in sorted(VALID_KEYS):
            val = data.get(key)
            if val is None:
                display = "[dim](not set)[/dim]"
            elif key == "api-key":
                display = "****"
            else:
                display = str(val)
            table.add_row(key, display)
        console.print(table)
    else:
        for key in sorted(VALID_KEYS):
            val = data.get(key)
            if val is None:
                display = ""
            elif key == "api-key" and val:
                display = "****"
            else:
                display = str(val)
            click.echo(f"{key}={display}")
