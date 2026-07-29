# chat Specification

## Purpose
Provides an interactive multi-turn chat REPL for the CLI, sending conversation history to the vLLM `/v1/chat/completions` endpoint. TBD: expand with additional context as the capability evolves.

## Requirements

### Requirement: Interactive multi-turn chat session
The `chat` subcommand SHALL start an interactive REPL loop that sends user messages to `/v1/chat/completions` and maintains conversation history for the duration of the session.

#### Scenario: Chat session starts
- **WHEN** user runs `vllm-cli chat`
- **THEN** the tool prints a welcome line and a `You: ` prompt, then waits for user input

#### Scenario: Assistant response displayed
- **WHEN** user types a message and presses Enter
- **THEN** the tool sends the full conversation history to `/v1/chat/completions` and prints the assistant's reply under `Assistant: `

#### Scenario: Conversation history maintained
- **WHEN** user sends multiple messages in one session
- **THEN** each subsequent request includes all prior user and assistant messages as context

### Requirement: Chat session system prompt
The `chat` subcommand SHALL accept an optional `--system` flag that sets the system prompt prepended to all requests in the session.

#### Scenario: System prompt included in request
- **WHEN** user runs `vllm-cli chat --system "You are a helpful coding assistant"`
- **THEN** every request includes a system message with that content as the first message

### Requirement: Chat session exit
The user SHALL be able to exit the chat session cleanly by typing `exit`, `quit`, or pressing Ctrl+C/Ctrl+D.

#### Scenario: Exit command ends session
- **WHEN** user types `exit` or `quit` at the prompt
- **THEN** the tool prints "Goodbye." and exits with code 0

#### Scenario: Ctrl+C ends session gracefully
- **WHEN** user presses Ctrl+C during a prompt or response
- **THEN** the tool exits with code 0 without printing a traceback

### Requirement: Chat session generation parameters
The `chat` subcommand SHALL support the same generation parameter flags as `complete`: `--max-tokens`, `--temperature`, `--top-p`.

#### Scenario: Temperature applied to chat requests
- **WHEN** user runs `vllm-cli chat --temperature 0.2`
- **THEN** every request in the session uses `temperature: 0.2`
