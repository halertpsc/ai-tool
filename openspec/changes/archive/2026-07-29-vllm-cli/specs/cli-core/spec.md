## ADDED Requirements

### Requirement: CLI entry point and command dispatch
The tool SHALL be invokable as `vllm-cli` and SHALL expose three top-level subcommands: `complete`, `chat`, and `config`. Running `vllm-cli` without a subcommand SHALL display help text listing all subcommands with brief descriptions.

#### Scenario: Help displayed with no subcommand
- **WHEN** user runs `vllm-cli` with no arguments
- **THEN** the tool prints help text listing `complete`, `chat`, and `config` subcommands and exits with code 0

#### Scenario: Unknown subcommand rejected
- **WHEN** user runs `vllm-cli unknown-command`
- **THEN** the tool prints an error message and exits with code 2

### Requirement: Global flags applicable to all subcommands
The tool SHALL support global flags that can be provided before any subcommand: `--url` (vLLM server base URL), `--model` (model identifier), `--api-key` (bearer token), and `--output` (output format: `text` or `json`). Global flags SHALL override values from the config file.

#### Scenario: Global URL flag overrides config
- **WHEN** user runs `vllm-cli --url http://myserver:8000 complete "hello"`
- **THEN** the tool sends the request to `http://myserver:8000` regardless of the configured URL

#### Scenario: JSON output flag applies globally
- **WHEN** user runs `vllm-cli --output json complete "hello"`
- **THEN** the tool prints raw JSON response from the API

### Requirement: Version flag
The tool SHALL support `--version` flag that prints the installed version string and exits with code 0.

#### Scenario: Version displayed
- **WHEN** user runs `vllm-cli --version`
- **THEN** the tool prints the version (e.g., `vllm-cli 0.1.0`) and exits with code 0
