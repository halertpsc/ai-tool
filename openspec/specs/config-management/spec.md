# config-management Specification

## Purpose
Manages persistent CLI configuration (server URL, model, API key, and generation defaults) via a TOML config file, `config` subcommands, and environment variable overrides. TBD: expand with additional context as the capability evolves.

## Requirements

### Requirement: Persistent configuration file
The tool SHALL store configuration in a TOML file at `~/.config/vllm-cli/config.toml` (Unix) or `%APPDATA%\vllm-cli\config.toml` (Windows). The file SHALL be created automatically on first write. If no config file exists, all settings MUST be provided via CLI flags or environment variables.

#### Scenario: Config file auto-created on first set
- **WHEN** user runs `vllm-cli config set url http://localhost:8000` and no config file exists
- **THEN** the tool creates the config directory and file, writes the value, and confirms with "Set url = http://localhost:8000"

#### Scenario: Missing required config surfaced clearly
- **WHEN** no URL is configured and user runs `vllm-cli complete "hello"` without `--url`
- **THEN** the tool prints "Error: server URL is not configured. Run `vllm-cli config set url <URL>` or use --url" and exits with code 1

### Requirement: config set subcommand
The `config set <key> <value>` command SHALL write a key-value pair to the config file. Supported keys: `url`, `model`, `api-key`, `max-tokens`, `temperature`.

#### Scenario: Setting URL persists
- **WHEN** user runs `vllm-cli config set url http://myserver:8000`
- **THEN** subsequent `vllm-cli complete` calls use `http://myserver:8000` without requiring `--url`

#### Scenario: Unknown key rejected
- **WHEN** user runs `vllm-cli config set unknown-key value`
- **THEN** the tool prints an error listing valid keys and exits with code 2

### Requirement: config get subcommand
The `config get <key>` command SHALL print the current value of a single config key to stdout.

#### Scenario: Get existing key
- **WHEN** user runs `vllm-cli config get url` after setting url
- **THEN** the tool prints the configured URL and exits with code 0

#### Scenario: Get unset key
- **WHEN** user runs `vllm-cli config get model` and model is not set
- **THEN** the tool prints "(not set)" and exits with code 0

### Requirement: config show subcommand
The `config show` command SHALL print all current configuration values in a readable table format, masking the `api-key` value.

#### Scenario: All values displayed
- **WHEN** user runs `vllm-cli config show`
- **THEN** the tool prints a table of all config keys and their values, with api-key shown as `****` if set

### Requirement: Environment variable overrides
The tool SHALL read configuration from environment variables (`VLLM_URL`, `VLLM_MODEL`, `VLLM_API_KEY`) with precedence: CLI flags > env vars > config file.

#### Scenario: Env var used as fallback
- **WHEN** `VLLM_URL=http://env-server:8000` is set and no `--url` flag is given
- **THEN** the tool uses `http://env-server:8000` as the server URL
