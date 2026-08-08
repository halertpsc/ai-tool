from pathlib import Path
from typing import Union

import httpx

from vllm_cli.tools.common import MAX_OUTPUT_CHARS, truncate_output

FETCH_TIMEOUT = 30.0
ALLOWED_SCHEMES = ("http", "https")


def fetch_url(tools_root: Union[str, Path], url: str) -> str:
    """Fetch `url` via HTTP GET. `tools_root` is accepted for handler-signature
    consistency with the filesystem/command tools but is not used here."""
    scheme = url.split("://", 1)[0].lower() if "://" in url else ""
    if scheme not in ALLOWED_SCHEMES:
        return f"Error: unsupported URL scheme in '{url}'; only http/https are allowed"

    try:
        resp = httpx.get(url, timeout=FETCH_TIMEOUT, follow_redirects=True)
    except httpx.HTTPError as exc:
        return f"Error: request to '{url}' failed: {exc}"

    body = truncate_output(resp.text, MAX_OUTPUT_CHARS)
    return f"HTTP {resp.status_code}\n\n{body}"
