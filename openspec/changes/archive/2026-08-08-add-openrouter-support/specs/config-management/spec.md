## MODIFIED Requirements

### Requirement: config set subcommand
The `config set <key> <value>` command SHALL write a key-value pair to the config file. Supported keys: `url`, `model`, `api-key`, `max-tokens`, `temperature`, `referer`, `title`.

#### Scenario: Setting URL persists
- **WHEN** user runs `vllm-cli config set url http://myserver:8000`
- **THEN** subsequent `vllm-cli complete` calls use `http://myserver:8000` without requiring `--url`

#### Scenario: Unknown key rejected
- **WHEN** user runs `vllm-cli config set unknown-key value`
- **THEN** the tool prints an error listing valid keys and exits with code 2

#### Scenario: Setting referer persists
- **WHEN** user runs `vllm-cli config set referer https://example.com`
- **THEN** subsequent API requests include the `HTTP-Referer: https://example.com` header

#### Scenario: Setting title persists
- **WHEN** user runs `vllm-cli config set title "My App"`
- **THEN** subsequent API requests include the `X-Title: My App` header

### Requirement: Environment variable overrides
The tool SHALL read configuration from environment variables (`VLLM_URL`, `VLLM_MODEL`, `VLLM_API_KEY`, `VLLM_REFERER`, `VLLM_TITLE`) with precedence: CLI flags > env vars > config file.

#### Scenario: Env var used as fallback
- **WHEN** `VLLM_URL=http://env-server:8000` is set and no `--url` flag is given
- **THEN** the tool uses `http://env-server:8000` as the server URL

#### Scenario: Referer and title env vars used as fallback
- **WHEN** `VLLM_REFERER=https://example.com` and `VLLM_TITLE=My App` are set and no `--referer`/`--title` flags are given
- **THEN** the tool sends `HTTP-Referer: https://example.com` and `X-Title: My App` headers on API requests

## ADDED Requirements

### Requirement: Optional attribution headers
The tool SHALL support optional `referer` and `title` configuration values. When set (via config file, environment variable, or CLI flag), the tool SHALL send them as `HTTP-Referer` and `X-Title` request headers respectively on every API call. When unset, the tool SHALL NOT send these headers. Unlike `api-key`, these values are not treated as sensitive.

#### Scenario: Headers omitted when unset
- **WHEN** neither `referer` nor `title` is configured by any source
- **THEN** API requests are sent without `HTTP-Referer` or `X-Title` headers

#### Scenario: Referer and title shown unmasked in config show
- **WHEN** user runs `vllm-cli config show` with `referer` and `title` set
- **THEN** the tool prints their plain-text values (not masked, unlike `api-key`)
