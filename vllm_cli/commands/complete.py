import json
import sys
from typing import Optional, Tuple

import click

from vllm_cli.client import VllmClient
from vllm_cli.config import require_url, resolve_settings
from vllm_cli.sse import StreamInterrupted, stream_to_stdout


@click.command()
@click.argument("prompt", required=False)
@click.option("--max-tokens", type=int, default=None, help="Max tokens to generate")
@click.option(
    "--temperature",
    type=click.FloatRange(0.0, 2.0),
    default=None,
    help="Sampling temperature (0.0–2.0)",
)
@click.option(
    "--top-p",
    type=click.FloatRange(0.0, 1.0),
    default=None,
    help="Top-p nucleus sampling (0.0–1.0)",
)
@click.option("--stop", multiple=True, help="Stop sequence (can be repeated)")
@click.option(
    "--stream/--no-stream",
    default=None,
    help="Stream output token by token (default: auto-detect TTY)",
)
@click.pass_context
def complete_cmd(
    ctx: click.Context,
    prompt: Optional[str],
    max_tokens: Optional[int],
    temperature: Optional[float],
    top_p: Optional[float],
    stop: Tuple[str, ...],
    stream: Optional[bool],
) -> None:
    """Send a single prompt to the model and print the completion."""
    if prompt is None:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        else:
            raise click.UsageError("PROMPT argument is required when stdin is a terminal.")

    settings = resolve_settings(ctx.obj)
    url = require_url(settings)
    model = settings.get("model") or "default"
    api_key = settings.get("api-key")
    output_fmt = ctx.obj.get("output") or "text"

    use_stream = stream if stream is not None else sys.stdout.isatty()

    params = {}
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    elif "max-tokens" in settings:
        params["max_tokens"] = int(settings["max-tokens"])
    if temperature is not None:
        params["temperature"] = temperature
    elif "temperature" in settings:
        params["temperature"] = float(settings["temperature"])
    if top_p is not None:
        params["top_p"] = top_p
    if stop:
        params["stop"] = list(stop)

    client = VllmClient(url, model, api_key)
    try:
        if use_stream and output_fmt != "json":
            try:
                stream_to_stdout(client.complete_stream(prompt, **params))
            except StreamInterrupted as exc:
                click.echo(f"\nStream interrupted: {exc}", err=True)
                sys.exit(1)
        else:
            result = client.complete(prompt, **params)
            if output_fmt == "json":
                click.echo(json.dumps(result, indent=2))
            else:
                text = result["choices"][0].get("text", "")
                click.echo(text)
    finally:
        client.close()
