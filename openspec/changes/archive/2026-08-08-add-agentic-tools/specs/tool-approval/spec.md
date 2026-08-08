## ADDED Requirements

### Requirement: Mandatory per-call approval before execution
Every attempt to execute a tool, regardless of which tool or how many times it has already been approved in the session, SHALL require an explicit user approval prompt before the tool's handler runs. There SHALL be no configuration flag, environment variable, or tool argument that bypasses this prompt.

#### Scenario: Approval required before any tool runs
- **WHEN** the model returns a tool call of any kind (file, web, or command tool)
- **THEN** the system presents an approval prompt to the user before invoking the corresponding tool handler

#### Scenario: Repeated calls to the same tool still prompt
- **WHEN** the model calls the same tool with the same or different arguments more than once in a session
- **THEN** each individual call is prompted for approval independently; no prior approval is reused

### Requirement: Approval prompt discloses tool name and arguments
The approval prompt SHALL display the tool's name and its fully resolved arguments (e.g., absolute file path, full command argv, target URL) before asking the user to approve or deny.

#### Scenario: Prompt shows resolved details
- **WHEN** the approval prompt is displayed for a `run_command` call
- **THEN** it shows the literal command that will be executed and the working directory it will run in

### Requirement: Denial prevents execution and is reported to the model
When the user denies an approval prompt, the system SHALL NOT execute the tool's handler, and SHALL return a `tool` role message to the model indicating the call was denied so the conversation can continue.

#### Scenario: Denied call not executed
- **WHEN** the user responds "no" to an approval prompt
- **THEN** the tool handler is not invoked and no side effect (file write, command run, network request) occurs

#### Scenario: Model informed of denial
- **WHEN** a tool call is denied
- **THEN** the next request to the model includes a tool result message stating the call was denied, allowing the model to respond accordingly

### Requirement: Approval required in both streaming and non-streaming modes
The approval gate SHALL apply identically whether the chat session is using streaming or non-streaming responses.

#### Scenario: Streaming session still prompts for approval
- **WHEN** a streaming chat response completes with one or more tool calls
- **THEN** the system prompts for approval on each tool call before executing any of them, the same as in non-streaming mode

### Requirement: Non-interactive sessions fail closed
If the chat session is running without an interactive terminal (unable to prompt the user), the system SHALL NOT execute any tool call and SHALL treat it as denied rather than silently approving it.

#### Scenario: No TTY available
- **WHEN** agentic mode is enabled but stdin/stdout is not an interactive terminal
- **THEN** any tool call the model requests is treated as denied and reported to the model as such, with no execution
