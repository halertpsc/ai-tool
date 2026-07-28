import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

VALID_KEYS = {"url", "model", "api-key", "max-tokens", "temperature"}

# CLI-facing key (hyphen) → TOML file key (underscore)
KEY_MAP = {
    "url": "url",
    "model": "model",
    "api-key": "api_key",
    "max-tokens": "max_tokens",
    "temperature": "temperature",
}

KEY_TYPES: Dict[str, type] = {
    "url": str,
    "model": str,
    "api-key": str,
    "max-tokens": int,
    "temperature": float,
}

ENV_MAP = {
    "url": "VLLM_URL",
    "model": "VLLM_MODEL",
    "api-key": "VLLM_API_KEY",
}

_REVERSE_KEY_MAP = {v: k for k, v in KEY_MAP.items()}


def get_config_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "vllm-cli" / "config.toml"


def config_read() -> Dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        data = tomllib.load(f)
    # Normalize underscore TOML keys back to CLI hyphen keys
    return {_REVERSE_KEY_MAP.get(k, k): v for k, v in data.items()}


def _format_toml_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(v)


def config_write(updates: Dict[str, Any]) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    current = config_read()
    current.update(updates)
    lines = [
        f"{KEY_MAP.get(k, k)} = {_format_toml_value(v)}"
        for k, v in current.items()
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_settings(cli_overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge config sources with priority: CLI flags > env vars > config file."""
    settings = config_read()
    for key, env_var in ENV_MAP.items():
        val = os.environ.get(env_var)
        if val is not None:
            settings[key] = val
    for key, val in (cli_overrides or {}).items():
        if val is not None:
            settings[key] = val
    return settings


def require_url(settings: Dict[str, Any]) -> str:
    url = settings.get("url")
    if not url:
        raise SystemExit(
            "Error: server URL is not configured. "
            "Run `vllm-cli config set url <URL>` or use --url"
        )
    return url
