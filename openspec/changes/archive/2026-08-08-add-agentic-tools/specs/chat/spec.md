## ADDED Requirements

### Requirement: Opt-in agentic mode flag
The `chat` subcommand SHALL accept a `--tools` flag (and corresponding `tools` config/env setting) that enables agentic mode for the session. Agentic mode SHALL be off by default.

#### Scenario: Tools disabled by default
- **WHEN** user runs `vllm-cli chat` without `--tools` and without `tools` configured
- **THEN** the session behaves exactly as before this change, with no tool schemas sent and no approval prompts possible

#### Scenario: Tools enabled via flag
- **WHEN** user runs `vllm-cli chat --tools`
- **THEN** the session sends built-in tool schemas with each request and is able to process tool calls from the model

### Requirement: Tools working directory flag
The `chat` subcommand SHALL accept a `--tools-root <dir>` flag that scopes filesystem and command tools to `<dir>` for the session, defaulting to the current working directory when not provided.

#### Scenario: Default tools root is launch directory
- **WHEN** user runs `vllm-cli chat --tools` without `--tools-root`
- **THEN** filesystem and command tools are scoped to the directory `vllm-cli` was launched from

### Requirement: Tool-call turn handling
When agentic mode is enabled and the model's response includes one or more tool calls, the `chat` subcommand SHALL, for each tool call in order: run the approval gate, execute the tool if approved, append the resulting `tool` role message(s) to the conversation history, and resend the updated history to the model. This SHALL repeat until a response contains no further tool calls, at which point the assistant's content is displayed as the reply.

#### Scenario: Single tool call resolved before reply
- **WHEN** the model responds with one tool call and, after approval and execution, is sent the tool result
- **THEN** the tool's subsequent reply (assistant content) is displayed to the user as the final "Assistant:" output for that turn

#### Scenario: Multiple sequential tool calls in one turn
- **WHEN** the model's response contains several tool calls
- **THEN** the system processes them one at a time (approval then execution) in the order returned, appending each tool result before resending

#### Scenario: Multi-round tool use
- **WHEN** the model's reply after receiving tool results itself contains further tool calls
- **THEN** the system continues the approve/execute/resend cycle until a reply contains no tool calls

### Requirement: Streaming tool-call accumulation
When agentic mode is enabled and streaming is active, the `chat` subcommand SHALL accumulate tool-call fragments delivered across multiple stream chunks into complete tool calls before beginning the approval flow, rather than approving or executing partial calls.

#### Scenario: Streamed tool call assembled before approval
- **WHEN** the model streams a tool call's name and arguments across multiple SSE chunks
- **THEN** the system waits until the stream signals the tool call is complete before presenting the approval prompt
