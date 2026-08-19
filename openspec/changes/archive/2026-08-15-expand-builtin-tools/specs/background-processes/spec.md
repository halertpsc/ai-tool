## ADDED Requirements

### Requirement: Start background process tool
The system SHALL provide a `start_process` tool that launches a subprocess within the tools working directory, keeps it running independently of the tool call that started it, and returns a process ID the model can reference in subsequent calls within the same session.

#### Scenario: Process started and ID returned
- **WHEN** the model calls `start_process` with a command and the call is approved
- **THEN** the tool launches the subprocess without waiting for it to exit and returns a process ID identifying it

#### Scenario: Concurrency cap enforced
- **WHEN** the number of currently tracked, still-running background processes is already at the configured cap
- **THEN** `start_process` returns an error result and does not spawn a new process

### Requirement: List background processes tool
The system SHALL provide a `list_processes` tool that returns the ID, command, and running/exited status of every background process tracked in the current session.

#### Scenario: Running and exited processes both listed
- **WHEN** the model calls `list_processes` and the call is approved
- **THEN** the tool returns every tracked process's ID, original command, and whether it is still running or has exited (with exit code if exited)

### Requirement: Read background process output tool
The system SHALL provide a `read_process_output` tool that returns a tracked process's stdout/stderr output accumulated since the previous read, plus its current running status, without blocking to wait for new output.

#### Scenario: Output drained since last read
- **WHEN** the model calls `read_process_output` with a process ID and the call is approved
- **THEN** the tool returns all output accumulated since the last read of that process (or since it started, if never read) and does not return that same output again on the next read

#### Scenario: Unknown process ID rejected
- **WHEN** the model calls `read_process_output` with a process ID that is not tracked in the current session
- **THEN** the tool returns an error result

#### Scenario: Output readable after process exit
- **WHEN** a tracked process has exited but produced output not yet read
- **THEN** `read_process_output` still returns that unread output along with the process's exit code

### Requirement: Background process output buffer is bounded
Each tracked background process's accumulated-but-unread output SHALL be held in a rolling buffer with a fixed maximum size, so an idle or unread long-lived process cannot grow memory usage without bound.

#### Scenario: Buffer cap exceeded
- **WHEN** a process produces more unread output than the buffer's maximum size before it is next read
- **THEN** the oldest unread output is dropped to stay within the cap, and the next `read_process_output` result notes that output was dropped

### Requirement: Send input to background process tool
The system SHALL provide a `send_process_input` tool that writes text to a tracked, still-running background process's stdin.

#### Scenario: Input written to a running process
- **WHEN** the model calls `send_process_input` with a process ID and text, the process is still running, and the call is approved
- **THEN** the tool writes the text to the process's stdin and returns a confirmation

#### Scenario: Writing to a stopped process rejected
- **WHEN** the model calls `send_process_input` for a process ID that has already exited
- **THEN** the tool returns an error result without attempting to write

### Requirement: Stop background process tool
The system SHALL provide a `stop_process` tool that terminates a tracked background process, escalating to a forceful kill if the process does not exit within a short grace period after a graceful terminate signal.

#### Scenario: Graceful stop
- **WHEN** the model calls `stop_process` with a process ID for a running process and the call is approved, and the process exits within the grace period
- **THEN** the tool reports the process as stopped with its exit code

#### Scenario: Escalation to forceful kill
- **WHEN** a process does not exit within the grace period after a graceful terminate signal
- **THEN** the tool forcefully kills the process and reports that a forceful kill was required

#### Scenario: Stopping an already-exited process
- **WHEN** the model calls `stop_process` for a process ID that has already exited
- **THEN** the tool returns a clear message that the process had already exited, rather than an error

### Requirement: Background processes scoped to the tools working directory
`start_process` SHALL launch subprocesses with their current working directory set to the configured tools working directory, consistent with `run_command`'s scoping.

#### Scenario: Process runs with scoped working directory
- **WHEN** the model calls `start_process` with a command
- **THEN** the subprocess is launched with its working directory set to the tools working directory

### Requirement: Background process tools require approval per call
Every `start_process`, `list_processes`, `read_process_output`, `send_process_input`, and `stop_process` call SHALL go through the same mandatory per-call approval gate as every other built-in tool; no call is pre-approved or batched because a prior call on the same process was approved.

#### Scenario: Each poll still prompts
- **WHEN** the model calls `read_process_output` on the same process ID multiple times across a session
- **THEN** each call is individually prompted for approval, the same as any other tool call

### Requirement: Background processes cleaned up on normal CLI exit
When the CLI process exits normally, all still-running background processes tracked in that session SHALL be terminated automatically.

#### Scenario: Normal exit terminates tracked children
- **WHEN** the CLI process exits normally while one or more background processes it started are still running
- **THEN** those processes are terminated as part of exit, rather than left running detached from the terminated session
