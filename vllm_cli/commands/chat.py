import sys
from typing import Dict, Generator, List, Optional

import click

from vllm_cli.client import VllmClient
from vllm_cli.config import require_url, resolve_settings
from vllm_cli.sse import StreamInterrupted


@click.command()
@click.option("--system", default=None, help="System prompt for the session")
@click.option("--max-tokens", type=int, default=None, help="Max tokens per response")
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
@click.pass_context
def chat_cmd(
    ctx: click.Context,
    system: Optional[str],
    max_tokens: Optional[int],
    temperature: Optional[float],
    top_p: Optional[float],
) -> None:
    """Start an interactive multi-turn chat session."""
    settings = resolve_settings(ctx.obj)
    url = require_url(settings)
    model = settings.get("model") or "default"
    api_key = settings.get("api-key")
    use_stream = sys.stdout.isatty()

    params: Dict = {}
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

    history: List[dict] = []
    if system:
        history.append({"role": "system", "content": system})

    client = VllmClient(url, model, api_key)
    click.echo(f"vllm-cli chat | model: {model} | type 'exit' or 'quit' to end\n")

    try:
        while True:
            try:
                user_input = click.prompt("You", prompt_suffix=": ")
            except (EOFError, KeyboardInterrupt):
                click.echo("\nGoodbye.")
                break

            stripped = user_input.strip()
            if stripped.lower() in ("exit", "quit"):
                click.echo("Goodbye.")
                break

            history.append({"role": "user", "content": stripped})
            click.echo("Assistant: ", nl=False)

            try:
                if use_stream:
                    reply = _stream_reply(client, list(history), params)
                else:
                    result = client.chat(list(history), **params)
                    reply = result["choices"][0]["message"]["content"]
                    click.echo(reply)
            except StreamInterrupted as exc:
                click.echo(f"\nStream interrupted: {exc}", err=True)
                sys.exit(1)

            if reply:
                history.append({"role": "assistant", "content": reply})

    except KeyboardInterrupt:
        click.echo("\nGoodbye.")
    finally:
        client.close()


def _stream_reply(client: VllmClient, history: List[dict], params: dict) -> str:
    """Stream chat response to stdout, return the full collected text."""
    collected: List[str] = []
    try:
        for token in client.chat_stream(history, **params):
            sys.stdout.write(token)
            sys.stdout.flush()
            collected.append(token)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except StreamInterrupted:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise
    return "".join(collected)
