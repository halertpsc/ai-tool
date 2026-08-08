## MODIFIED Requirements

### Requirement: Global flags applicable to all subcommands
The tool SHALL support global flags that can be provided before any subcommand: `--url` (server base URL), `--model` (model identifier), `--api-key` (bearer token), `--referer` (value sent as the `HTTP-Referer` header), `--title` (value sent as the `X-Title` header), and `--output` (output format: `text` or `json`). Global flags SHALL override values from environment variables and the config file.

#### Scenario: Global URL flag overrides config
- **WHEN** user runs `vllm-cli --url http://myserver:8000 complete "hello"`
- **THEN** the tool sends the request to `http://myserver:8000` regardless of the configured URL

#### Scenario: JSON output flag applies globally
- **WHEN** user runs `vllm-cli --output json complete "hello"`
- **THEN** the tool prints raw JSON response from the API

#### Scenario: Global referer and title flags override config
- **WHEN** user runs `vllm-cli --referer https://example.com --title "My App" complete "hello"`
- **THEN** the tool sends `HTTP-Referer: https://example.com` and `X-Title: My App` headers regardless of configured values
