# streaming Specification

## Purpose
Provides streaming token output for `complete` and `chat` via Server-Sent Events from the vLLM API, including SSE parsing and stream error handling. TBD: expand with additional context as the capability evolves.

## Requirements

### Requirement: Streaming output for completion and chat
Both `complete` and `chat` subcommands SHALL support a `--stream` flag (default: enabled when stdout is a TTY) that requests streaming responses from the vLLM API using `stream: true`. Tokens SHALL be printed to stdout as they arrive without buffering.

#### Scenario: Streaming tokens printed incrementally
- **WHEN** user runs `vllm-cli complete "Tell me a story" --stream`
- **THEN** the tool prints each token to stdout as it is received from the SSE stream, without waiting for the full response

#### Scenario: Non-streaming when piped
- **WHEN** stdout is not a TTY (e.g., `vllm-cli complete "hello" > output.txt`)
- **THEN** the tool defaults to non-streaming mode and writes the complete response once finished

#### Scenario: Streaming explicitly disabled
- **WHEN** user runs `vllm-cli complete "hello" --no-stream`
- **THEN** the tool waits for the full response before printing, even if stdout is a TTY

### Requirement: SSE stream parsing
The tool SHALL parse Server-Sent Events format from the vLLM streaming response. Each `data:` line SHALL be decoded as JSON and the delta token extracted. The stream SHALL terminate on receiving `data: [DONE]`.

#### Scenario: Partial tokens assembled correctly
- **WHEN** the SSE stream delivers tokens across multiple chunks
- **THEN** the tool prints each delta token immediately upon receipt without dropping or duplicating tokens

#### Scenario: Stream terminated on DONE sentinel
- **WHEN** the server sends `data: [DONE]`
- **THEN** the tool stops reading the stream and exits cleanly

### Requirement: Streaming error handling
If the stream is interrupted (connection dropped mid-response), the tool SHALL print a newline, display "Stream interrupted: <reason>", and exit with code 1.

#### Scenario: Interrupted stream handled gracefully
- **WHEN** the server closes the connection before sending `[DONE]`
- **THEN** the tool prints whatever tokens were received, then prints "Stream interrupted: connection closed" on a new line and exits with code 1
