from importlib.metadata import PackageNotFoundError, version

import click

from vllm_cli.commands.chat import chat_cmd
from vllm_cli.commands.complete import complete_cmd
from vllm_cli.commands.config_cmd import config_group

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
