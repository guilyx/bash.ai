# Architecture of Flourish

## Overview

Flourish is an AI-powered terminal environment enhancement tool designed to provide an intelligent assistant directly within the terminal. It leverages Large Language Models (LLMs) to understand user requests, execute bash commands, and manage a secure environment through allowlists and blacklists. The architecture is modular, allowing for easy extension and integration with various LLM providers via LiteLLM.

## Core Components

The system is composed of several key Python packages:

1. **`bash_ai.config`**:
   - **Purpose**: Manages application settings, environment variables, and persistent configuration (allowlist/blacklist).
   - **Details**: Loads settings from `.env` files and manages `config/commands.json` for dynamic command restrictions.

2. **`bash_ai.agent`**:
   - **Purpose**: Defines the AI agent's behavior, system instructions, and interaction logic with the LLM.
   - **Details**: Constructs the system prompt, including dynamic allowlist/blacklist rules. It uses LiteLLM to communicate with various LLM providers.

3. **`bash_ai.tools`**:
   - **Purpose**: Provides custom Python functions that the AI agent can call to interact with the bash environment and manage command lists.
   - **Details**: Includes `execute_bash`, `set_cwd`, `add_to_allowlist`, `add_to_blacklist`, etc. These tools incorporate pre-execution validation against the allowlist/blacklist.

4. **`bash_ai.runner`**:
   - **Purpose**: Orchestrates the interaction between the user, the AI agent, and the tools.
   - **Details**: Handles sending user prompts to the agent, processing streaming responses, and logging the conversation and tool calls. It acts as the bridge between the UI and the core agent logic.

5. **`bash_ai.ui`**:
   - **Purpose**: Implements the Terminal User Interface (TUI) and the command-line interface (CLI).
   - **Details**: The TUI provides an interactive terminal environment where users can execute bash commands directly and request AI assistance using the `?` prefix or `Ctrl+A`. Commands execute immediately via subprocess, while AI requests are routed to the agent. The CLI offers non-interactive command-line interaction for scripting and automation.

6. **`bash_ai.logging`**:
   - **Purpose**: Manages structured logging for sessions, conversations, and tool executions.
   - **Details**: Creates timestamped log files in `~/.config/flourish/logs/` and records detailed events for debugging and auditing.

## Data Flow and Interaction

1. **Initialization**:
   - The Flourish application starts (either TUI or CLI).
   - `bash_ai.config` loads settings from `.env` and `config/commands.json`.
   - `bash_ai.logging` initializes a new session log file.

2. **User Input**:
   - **Terminal Mode**: The user types commands directly in the TUI terminal. Regular bash commands (e.g., `ls`, `cd`, `git status`) execute immediately via subprocess. AI requests (prefixed with `?` or triggered via `Ctrl+A`) are sent to the agent.
   - **CLI Mode**: The user provides a prompt via command-line arguments.
   - The `bash_ai.ui` component captures the input and determines whether to execute directly or route to the agent.
   - `bash_ai.logging` records user commands and AI requests.

3. **Agent Processing**:
   - The `bash_ai.runner` sends the user's prompt to the `bash_ai.agent`.
   - The `bash_ai.agent` constructs a system prompt (including dynamic allowlist/blacklist rules from `bash_ai.config`).
   - The agent uses `LiteLLM` to send the prompt and system instructions to the configured LLM (e.g., Gemini, GPT).

4. **LLM Response and Tool Calling**:
   - The LLM processes the request and generates a response, which might include a decision to call one of the `bash_ai.tools`.
   - If a tool call is suggested (e.g., `execute_bash`), the `bash_ai.runner` intercepts it.

5. **Tool Execution and Validation**:
   - Before executing `execute_bash`, the `bash_ai.tools` module performs a critical security check:
     - It verifies the command against the `blacklist` (always blocked).
     - It checks against the `allowlist`. If the command is not in the allowlist, it triggers a confirmation flow.
   - If confirmation is needed, the system (via `ToolContext.request_confirmation`) prompts the user.
   - **Automated Allowlist Management**: If a command is not in the allowlist and requires confirmation, the agent is instructed to *automatically* call `add_to_allowlist` (after user confirmation for the add operation itself) and then re-execute the original command.
   - `bash_ai.logging` records all tool calls, their parameters, and results.

6. **Output and Display**:
   - **Direct Command Execution**: For regular bash commands, output (stdout/stderr) is displayed immediately in the terminal with color coding (green for commands, white for output, red for errors).
   - **AI Responses**: The results from tool execution (stdout, stderr, status) or direct LLM text responses are sent back to the `bash_ai.runner`.
   - The `bash_ai.runner` streams or sends the complete response to the `bash_ai.ui`.
   - The `bash_ai.ui` displays AI responses in cyan, maintaining the terminal aesthetic.
   - `bash_ai.logging` records all commands, tool calls, and agent responses.

## Security Model

The security of Flourish is paramount, especially given its ability to execute arbitrary shell commands.

- **Allowlist/Blacklist**: The core security mechanism.
  - **Blacklist**: Commands explicitly forbidden (e.g., `rm`, `dd`). These are hard-blocked.
  - **Allowlist**: Commands explicitly permitted. If an allowlist is active, only commands on this list can be executed.
  - **Pre-execution Validation**: All commands are validated *before* execution by the `bash_ai.tools` module.
- **User Confirmation**: For commands not in the allowlist (when an allowlist is active), the system requires explicit user confirmation before execution. This is handled by the system, not the agent, to prevent the agent from bypassing security.
- **Automated Allowlist Management**: The agent is instructed to proactively add safe, frequently used commands to the allowlist (after system-level confirmation for the add operation), improving workflow efficiency while maintaining security.
- **Permissions**: The agent operates with the same user permissions as the Flourish application itself. It does not elevate privileges.
- **API Key Security**: API keys are loaded from `.env` files and never committed to version control.

## Extensibility

- **LiteLLM**: Allows easy switching between different LLM providers by changing the `MODEL` environment variable.
- **Modular Tools**: New bash tools can be added by creating Python functions in `bash_ai.tools` and ensuring they are exposed to the agent.
- **Configuration**: The `config/commands.json` provides a flexible way to manage command restrictions.
