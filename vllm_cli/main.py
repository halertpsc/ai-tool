import sys
from importlib.metadata import PackageNotFoundError, version

import click

from vllm_cli.commands.chat import chat_cmd
from vllm_cli.commands.complete import complete_cmd
from vllm_cli.commands.config_cmd import config_group

# Model I/O is UTF-8 and may contain characters outside the default Windows
# console code page (cp1252): output containing them would otherwise raise
# UnicodeEncodeError, and input containing them would otherwise be silently
# mis-decoded (each UTF-8 byte read back as a separate cp1252 character).
# Reconfigure stdio to UTF-8 so both directions round-trip correctly.
for _stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

try:
    _version = version("vllm-cli")
except PackageNotFoundError:
    _version = "0.1.0"


@click.group()
@click.version_option(_version, "--version", prog_name="vllm-cli")
@click.option("--url", default=None, help="vLLM server base URL")
@click.option("--model", default=None, help="Model identifier")
@click.option("--api-key", default=None, help="Bearer token for authentication")
@click.option("--referer", default=None, help="Value sent as the HTTP-Referer header")
@click.option("--title", default=None, help="Value sent as the X-Title header")
@click.option(
    "--output",
    default=None,
    type=click.Choice(["text", "json"]),
    help="Output format (text or json)",
)
@click.pass_context
def cli(
    ctx: click.Context,
    url: str,
    model: str,
    api_key: str,
    referer: str,
    title: str,
    output: str,
) -> None:
    """Command-line interface for vLLM-hosted models."""
    ctx.ensure_object(dict)
    ctx.obj["url"] = url
    ctx.obj["model"] = model
    ctx.obj["api-key"] = api_key
    ctx.obj["referer"] = referer
    ctx.obj["title"] = title
    ctx.obj["output"] = output


cli.add_command(complete_cmd, name="complete")
cli.add_command(chat_cmd, name="chat")
cli.add_command(config_group, name="config")
