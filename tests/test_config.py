import os
from pathlib import Path

import pytest

import vllm_cli.config as cfg_module
from vllm_cli.config import config_read, config_write, require_url, resolve_settings


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
