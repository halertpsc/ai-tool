import os
from pathlib import Path

import pytest

import vllm_cli.config as cfg_module
from vllm_cli.config import coerce_bool, config_read, config_write, require_url, resolve_settings


@pytest.fixture(autouse=True)
def tmp_config(tmp_path, monkeypatch):
    config_file = tmp_path / "vllm-cli" / "config.toml"
    monkeypatch.setattr(cfg_module, "get_config_path", lambda: config_file)
    return config_file


def test_missing_config_returns_empty():
    assert config_read() == {}


def test_write_and_read_roundtrip():
    config_write({"url": "http://localhost:8000", "model": "llama3"})
    result = config_read()
    assert result["url"] == "http://localhost:8000"
    assert result["model"] == "llama3"


def test_write_creates_parent_dirs(tmp_config):
    assert not tmp_config.parent.exists()
    config_write({"url": "http://x"})
    assert tmp_config.exists()


def test_write_merges_with_existing():
    config_write({"url": "http://a"})
    config_write({"model": "gpt2"})
    result = config_read()
    assert result["url"] == "http://a"
    assert result["model"] == "gpt2"


def test_resolve_settings_env_overrides_file(monkeypatch):
    config_write({"url": "http://from-file"})
    monkeypatch.setenv("VLLM_URL", "http://from-env")
    settings = resolve_settings({})
    assert settings["url"] == "http://from-env"


def test_resolve_settings_cli_overrides_env(monkeypatch):
    config_write({"url": "http://from-file"})
    monkeypatch.setenv("VLLM_URL", "http://from-env")
    settings = resolve_settings({"url": "http://from-cli"})
    assert settings["url"] == "http://from-cli"


def test_resolve_settings_none_cli_does_not_override():
    config_write({"url": "http://from-file"})
    settings = resolve_settings({"url": None})
    assert settings["url"] == "http://from-file"


def test_require_url_raises_when_missing():
    with pytest.raises(SystemExit, match="not configured"):
        require_url({})


def test_require_url_returns_value():
    assert require_url({"url": "http://localhost:8000"}) == "http://localhost:8000"


def test_api_key_hyphen_roundtrip():
    config_write({"api-key": "secret"})
    result = config_read()
    assert result["api-key"] == "secret"


def test_max_tokens_int_roundtrip():
    config_write({"max-tokens": 512})
    result = config_read()
    assert result["max-tokens"] == 512


def test_referer_roundtrip():
    config_write({"referer": "https://example.com"})
    result = config_read()
    assert result["referer"] == "https://example.com"


def test_title_roundtrip():
    config_write({"title": "My App"})
    result = config_read()
    assert result["title"] == "My App"


def test_resolve_settings_referer_title_priority(monkeypatch):
    config_write({"referer": "https://from-file", "title": "from-file"})
    monkeypatch.setenv("VLLM_REFERER", "https://from-env")
    monkeypatch.setenv("VLLM_TITLE", "from-env")
    settings = resolve_settings({})
    assert settings["referer"] == "https://from-env"
    assert settings["title"] == "from-env"

    settings = resolve_settings({"referer": "https://from-cli", "title": "from-cli"})
    assert settings["referer"] == "https://from-cli"
    assert settings["title"] == "from-cli"


def test_tools_bool_roundtrip():
    config_write({"tools": True})
    result = config_read()
    assert result["tools"] is True


def test_tools_root_roundtrip():
    config_write({"tools-root": "/some/dir"})
    result = config_read()
    assert result["tools-root"] == "/some/dir"


def test_resolve_settings_tools_env_var(monkeypatch):
    monkeypatch.setenv("VLLM_TOOLS", "true")
    monkeypatch.setenv("VLLM_TOOLS_ROOT", "/env/dir")
    settings = resolve_settings({})
    assert settings["tools"] == "true"
    assert settings["tools-root"] == "/env/dir"


def test_coerce_bool_variants():
    assert coerce_bool(True) is True
    assert coerce_bool(False) is False
    assert coerce_bool(None) is False
    assert coerce_bool("true") is True
    assert coerce_bool("True") is True
    assert coerce_bool("1") is True
    assert coerce_bool("yes") is True
    assert coerce_bool("false") is False
    assert coerce_bool("0") is False
    assert coerce_bool("") is False
