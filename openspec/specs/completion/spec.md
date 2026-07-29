# completion Specification

## Purpose
Provides single-turn text completion via the vLLM `/v1/completions` endpoint, including generation parameters and error handling. TBD: expand with additional context as the capability evolves.

## Requirements

### Requirement: Single-turn text completion
The `complete` subcommand SHALL accept a prompt as a positional argument and send it to the vLLM `/v1/completions` endpoint, printing the generated text to stdout.

#### Scenario: Successful completion
- **WHEN** user runs `vllm-cli complete "What is the capital of France?"`
- **THEN** the tool sends a POST to `/v1/completions` with the prompt and prints the completion text to stdout

#### Scenario: Prompt read from stdin
- **WHEN** user pipes input: `echo "Tell me a joke" | vllm-cli complete`
- **THEN** the tool reads the prompt from stdin and sends it to the completions endpoint

### Requirement: Completion generation parameters
The `complete` subcommand SHALL support optional flags to control generation: `--max-tokens` (integer, default 256), `--temperature` (float 0.0–2.0, default 1.0), `--top-p` (float 0.0–1.0), and `--stop` (string, repeatable, stop sequences).

#### Scenario: Custom max tokens respected
- **WHEN** user runs `vllm-cli complete "Hello" --max-tokens 50`
- **THEN** the request includes `max_tokens: 50` and the response is limited accordingly

#### Scenario: Invalid temperature rejected
- **WHEN** user runs `vllm-cli complete "Hello" --temperature 5.0`
- **THEN** the tool prints a validation error and exits with code 2

### Requirement: Completion error handling
The `complete` subcommand SHALL print a human-readable error message and exit with code 1 when the API returns a non-2xx HTTP status or when the server is unreachable.

#### Scenario: Server unreachable
- **WHEN** the vLLM server is not running at the configured URL
- **THEN** the tool prints "Connection error: could not reach <url>" and exits with code 1

#### Scenario: API error response
- **WHEN** the API returns a 400 or 500 error
- **THEN** the tool prints the HTTP status code and the error message from the response body, then exits with code 1
