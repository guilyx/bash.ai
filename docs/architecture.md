# Architecture of Flouri

## Overview

Flouri is an AI-powered terminal environment enhancement tool designed to provide an intelligent assistant directly within the terminal. It leverages Large Language Models (LLMs) to understand user requests, execute bash commands, and manage a secure environment through allowlists and blacklists. The architecture is modular, allowing for easy extension and integration with various LLM providers via LiteLLM.

## Core Components

The system is composed of several key Python packages:

1. **`flouri.config`**:
   - **Purpose**: Manages application settings, environment variables, and persistent configuration (allowlist/blacklist).
   - **Details**: Loads settings from `.env` files and manages `config/commands.json` for dynamic command restrictions.

2. **`flouri.agent`**:
   - **Purpose**: Defines the AI agent's behavior, system instructions, and interaction logic with the LLM.
   - **Details**: Constructs the system prompt, including dynamic allowlist/blacklist rules. It uses LiteLLM to communicate with various LLM providers.

3. **`flouri.tools`**:
   - **Purpose**: Provides custom Python functions that the AI agent can call to interact with the bash environment and manage command lists.
   - **Details**: Organized into modular subdirectories by context:
     - `tools/bash/`: Bash execution tools (`execute_bash`, `set_cwd`, `get_user`)
     - `tools/config/`: Configuration and allowlist/blacklist management (`add_to_allowlist`, `add_to_blacklist`, `list_allowlist`, etc.)
     - `tools/history/`: History-related tools (`read_bash_history`, `read_conversation_history`)
     - `tools/system/`: System information tools (`get_current_datetime`)
     - `tools/globals.py`: Shared global variables (`GLOBAL_CWD`, `GLOBAL_ALLOWLIST`, `GLOBAL_BLACKLIST`)
   - All tools incorporate pre-execution validation against the allowlist/blacklist.

4. **`flouri.runner`**:
   - **Purpose**: Orchestrates the interaction between the user, the AI agent, and the tools.
   - **Details**: Handles sending user prompts to the agent, processing streaming responses, and logging the conversation and tool calls. It acts as the bridge between the UI and the core agent logic.

5. **`flouri.ui`**:
   - **Purpose**: Implements the Terminal User Interface (TUI) and the command-line interface (CLI).
   - **Details**: The TUI provides an interactive terminal environment where users can execute bash commands directly and request AI assistance using the `?` prefix or `Ctrl+A`. Commands execute immediately via subprocess, while AI requests are routed to the agent. The CLI offers non-interactive command-line interaction for scripting and automation. The TUI is built with `prompt-toolkit` for rich terminal interactions, including command completion and history.

6. **`flouri.completions`**:
   - **Purpose**: Provides bash-style command completion system with support for custom completion scripts.
   - **Details**: Includes a completion registry and loader that can discover and load completion scripts from project and user directories. Supports built-in completions (e.g., `cd` with nested directory support, `git` command completions) and extensible custom completions. Completion scripts follow a standard interface and can be placed in `completions/` or `~/.config/flouri/completions/`.

7. **`flouri.logging`**:
   - **Purpose**: Manages structured logging for sessions, conversations, and tool executions.
   - **Details**: Creates timestamped log files in `~/.config/flouri/logs/` and records detailed events for debugging and auditing.

## Data Flow and Interaction

1. **Initialization**:
   - The Flouri application starts (either TUI or CLI).
   - `flouri.config` loads settings from `.env` and `config/commands.json`.
   - `flouri.logging` initializes a new session log file.
   - `flouri.completions` loads completion scripts from project and user directories.
   - `flouri.plugins` registers built-in plugins (e.g., `ZshBindingsPlugin`, `CdCompleter`, enhancers).

2. **User Input**:
   - **Terminal Mode**: The user types commands directly in the TUI terminal. The `prompt-toolkit` interface provides:
     - Tab completion via `flouri.completions` (e.g., `cd` with nested directory support, `git` command completions)
     - Command history navigation
     - Syntax highlighting via Pygments
   - Regular bash commands (e.g., `ls`, `cd`, `git status`) execute immediately via subprocess. AI requests (prefixed with `?` or triggered via `Ctrl+A`) are sent to the agent.
   - **CLI Mode**: The user provides a prompt via command-line arguments.
   - The `flouri.ui` component captures the input and determines whether to execute directly or route to the agent.
   - `flouri.logging` records user commands and AI requests.

3. **Agent Processing**:
   - The `flouri.runner` sends the user's prompt to the `flouri.agent`.
   - The `flouri.agent` constructs a system prompt (including dynamic allowlist/blacklist rules from `flouri.config`).
   - The agent uses `LiteLLM` to send the prompt and system instructions to the configured LLM (e.g., Gemini, GPT).

4. **LLM Response and Tool Calling**:
   - The LLM processes the request and generates a response, which might include a decision to call one of the `flouri.tools`.
   - If a tool call is suggested (e.g., `execute_bash`), the `flouri.runner` intercepts it.

5. **Tool Execution and Validation**:
   - Before executing `execute_bash`, the `flouri.tools` module performs a critical security check:
     - It verifies the command against the `blacklist` (always blocked).
     - It checks against the `allowlist`. If the command is not in the allowlist, it triggers a confirmation flow.
   - If confirmation is needed, the system (via `ToolContext.request_confirmation`) prompts the user.
   - **Automated Allowlist Management**: If a command is not in the allowlist and requires confirmation, the agent is instructed to *automatically* call `add_to_allowlist` (after user confirmation for the add operation itself) and then re-execute the original command.
   - `flouri.logging` records all tool calls, their parameters, and results.

6. **Output and Display**:
   - **Direct Command Execution**: For regular bash commands, output (stdout/stderr) is processed by `flouri.plugins` enhancers (e.g., `LsColorEnhancer` for colored `ls` output, `CdEnhancementPlugin` for `cd` hints). The enhanced output is displayed immediately in the terminal with color coding (green for commands, white for output, red for errors).
   - **AI Responses**: The results from tool execution (stdout, stderr, status) or direct LLM text responses are sent back to the `flouri.runner`.
   - The `flouri.runner` streams or sends the complete response to the `flouri.ui`.
   - The `flouri.ui` displays AI responses in cyan, maintaining the terminal aesthetic.
   - `flouri.logging` records all commands, tool calls, and agent responses.

## Security Model

The security of Flouri is paramount, especially given its ability to execute arbitrary shell commands.

- **Allowlist/Blacklist**: The core security mechanism.
  - **Blacklist**: Commands explicitly forbidden (e.g., `rm`, `dd`). These are hard-blocked.
  - **Allowlist**: Commands explicitly permitted. If an allowlist is active, only commands on this list can be executed.
  - **Pre-execution Validation**: All commands are validated *before* execution by the `flouri.tools` module.
- **User Confirmation**: For commands not in the allowlist (when an allowlist is active), the system requires explicit user confirmation before execution. This is handled by the system, not the agent, to prevent the agent from bypassing security.
- **Automated Allowlist Management**: The agent is instructed to proactively add safe, frequently used commands to the allowlist (after system-level confirmation for the add operation), improving workflow efficiency while maintaining security.
- **Permissions**: The agent operates with the same user permissions as the Flouri application itself. It does not elevate privileges.
- **API Key Security**: API keys are loaded from `.env` files and never committed to version control.

## Extensibility

- **LiteLLM**: Allows easy switching between different LLM providers by changing the `MODEL` environment variable.
- **Google ADK**: Provides the agent framework for orchestration, tool calling, and session management.
- **Modular Tools**: New tools can be added by creating Python functions in the appropriate `flouri.tools` subdirectory (e.g., `tools/bash/` for bash commands, `tools/system/` for system info) and ensuring they are exposed via `tools/__init__.py` and `get_bash_tools()`.
- **Plugin System**: Extend functionality with custom plugins (command handlers and enhancers) - see `docs/plugins.md`.
- **Completion System**: Add custom command completions by creating completion scripts in `completions/` or `~/.config/flouri/completions/`.
- **Configuration**: The `config/commands.json` provides a flexible way to manage command restrictions.
