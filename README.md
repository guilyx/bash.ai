# Flourish (flouri.sh)

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-yellow.svg)](https://github.com/astral-sh/ruff)

```bash
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║  ███████╗██╗      ██████╗ ██╗   ██╗██████╗ ██╗███████╗██╗  ██╗         ║
║  ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗██║██╔════╝██║  ██║         ║
║  █████╗  ██║     ██║   ██║██║   ██║██████╔╝██║███████╗███████║         ║
║  ██╔══╝  ██║     ██║   ██║██║   ██║██╔══██╗██║╚════██║██╔══██║         ║
║  ██║     ███████╗╚██████╔╝╚██████╔╝██║  ██║██║███████║██║  ██║         ║
║  ╚═╝     ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝         ║
║                                                                        ║
║                    AI-Powered Terminal Environment                     ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
```

Flourish is an open-source tool that enhances your terminal environment with agentic AI capabilities. It allows you to interact with various LLMs directly from your terminal and execute complex workflows through AI orchestration.

## Features

- **Terminal Environment**: AI-enabled terminal that looks and feels like a real bash terminal
  - Execute commands directly (e.g., `ls`, `git status`, `cd ~/projects`)
  - AI assistance available on-demand with `?` prefix or `Ctrl+A`
  - Real-time command output with color-coded results

- **AI Assistance**: Get help from AI without leaving your terminal
  ```bash
  $ ? explain the difference between git merge and rebase
  $ ? how do I check disk usage?
  $ ? help me write a script to find large files
  ```

- **Direct Command Execution**: Run bash commands immediately - no agent wrapper needed
  ```bash
  $ ls -la
  $ git status
  $ cd ~/projects
  ```

- **Smart Completions**: Bash-style tab completion with support for custom completion scripts
  - Built-in completions for common commands (cd, git, etc.)
  - Extensible completion system for custom commands
  - Nested directory completion for `cd` command

- **Security Controls**: Allowlist and blacklist for AI-executed commands (when AI runs commands via tools)

## Prerequisites

- Python 3.10 or later (3.12+ recommended)
- An API key for your chosen LLM provider (e.g., OpenAI, Anthropic, Google)

### Upgrading Python

If you need to upgrade Python, you can use:

```bash
# Using pyenv (recommended)
pyenv install 3.12.0
pyenv global 3.12.0

# Or download from python.org
```

## Quick Start

1. **Install and configure**:
   ```bash
   git clone https://github.com/made-after-dark/flourish.git
   cd flourish
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   cp env.example .env
   # Edit .env and add your API_KEY
   ```

2. **Launch the terminal**:
   ```bash
   flourish
   ```

   When you launch Flourish, you'll see:
   - A beautiful ASCII banner animation
   - Welcome message with usage hints
   - Your current directory in the prompt
   - Git branch information (if in a git repository)
   - Command history automatically loaded from previous sessions

3. **Start using it**:
   ```bash
   $ ls -la                    # Execute commands directly
   $ ? explain git merge       # Ask AI for help
   $ git status                # Normal bash commands work
   $ Ctrl+A                    # Or press Ctrl+A to ask AI
   ```

## Installation

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/made-after-dark/flourish.git
   cd flourish
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Set up your API key:
   ```bash
   cp env.example .env
   # Edit .env and add your API_KEY and preferred MODEL
   ```

   The `.env` file is automatically loaded - no need to `source` it!

5. (Optional) Install pre-commit hooks for code quality:
   ```bash
   pre-commit install
   ```

## Usage Examples

### Daily Workflow Examples

```bash
# Navigate and explore
$ cd ~/projects/myapp
$ ls -la                    # Color-coded file listing
$ cd src/components         # Tab completion for nested paths

# Git operations with AI help
$ ? how do I squash the last 3 commits?
$ git log --oneline
$ ? create a commit message for these changes: [paste diff]

# File operations
$ find . -name "*.py" -type f
$ ? show me the largest files in this directory
$ cat config.json | ? explain what this configuration does

# Development tasks
$ ? help me set up a Python virtual environment
$ ? write a script to backup my dotfiles
$ ? explain the difference between async and await in Python
```

### Advanced Usage

```bash
# Combine commands with AI
$ ls -la && ? explain what each file in this directory does

# AI-assisted debugging
$ python script.py
$ ? the script failed with error X, how do I fix it?

# Project management
$ ? analyze this project and suggest a better directory structure
$ ? generate a README for this project based on the code
$ ? what dependencies does this project need?
```

### Terminal Interface (TUI) - Recommended

Launch the AI-enabled terminal environment:

```bash
flourish
# or
flourish tui
```

#### What Happens When You Open Flourish?

When you launch Flourish, the following happens:

1. **Banner Display**: An animated ASCII banner welcomes you
2. **Configuration Loading**:
   - Environment variables from `.env` are loaded
   - Command allowlist/blacklist from `config/commands.json` is loaded
   - Session logging is initialized
3. **Plugin System Initialization**:
   - Built-in plugins are registered (zsh bindings, command enhancers)
   - Completion system loads custom completion scripts
4. **History Restoration**:
   - Command history is loaded from `~/.config/flourish/history`
   - Previous session commands are available via arrow keys
5. **Ready to Use**: You're presented with a prompt showing:
   - Current working directory
   - Git branch (if in a git repository)
   - Git status indicators (if applicable)

#### Interactive Terminal Features

This opens an interactive terminal where you can:

1. **Execute commands directly** (just like a normal terminal):
   ```bash
   $ ls -la                           # List files with details
   $ git status                       # Check git status
   $ cd ~/projects                    # Change directory
   $ pwd                              # Print working directory
   $ cat README.md                    # View file contents
   $ grep -r "function" src/          # Search in files
   $ find . -name "*.py"              # Find Python files
   ```

2. **Get AI assistance** using the `?` prefix:
   ```bash
   $ ? explain the difference between git merge and rebase
   $ ? how do I check disk usage?
   $ ? help me write a script to find large files
   $ ? what's the best way to organize this project?
   $ ? show me how to use docker compose
   ```

3. **Use keyboard shortcuts**:
   - `Ctrl+A` - Start an AI prompt
   - `Tab` - Auto-complete commands and paths (with nested directory support)
   - `↑/↓` - Navigate command history
   - `Ctrl+R` - Reverse search through history (fzf-like)
   - `Ctrl+L` - Clear screen (preserves welcome message)
   - `Ctrl+D` - Exit Flourish
   - `Ctrl+C` - Cancel current operation

4. **Enhanced Features**:
   ```bash
   $ cd                              # Goes to home directory (zsh-like)
   $ cd ...                          # Goes back 2 directories
   $ cd ....                         # Goes back 3 directories
   $ ls                              # Color-coded output (directories, executables, etc.)
   $ git checkout <TAB>             # Smart git command completion
   ```

### Command-Line Interface (CLI)

For non-interactive use or scripting:

```bash
# Ask questions (AI responds with text)
flourish agent "Explain how Docker containers work"

# Ask questions with command execution
flourish agent "Show me git status and list all Python files"

# With allowlist (only allow specific commands for AI execution)
flourish agent --allowlist "ls,cd,git,find" "Show me git status and list files"

# With blacklist (prevent specific commands)
flourish agent --blacklist "rm,dd,format" "Help me organize my project files"

# With live streaming (real-time output as AI generates response)
flourish agent --stream "Explain how Docker containers work"
flourish agent -s "List files and show git status"  # Short form

# Complex workflows
flourish agent "Analyze my project structure and suggest improvements"
flourish agent "Find all TODO comments in the codebase and create a summary"
```

#### Example CLI Workflows

```bash
# Development workflow
flourish agent "Check git status, run tests, and show me any failing tests"

# File management
flourish agent "Find all large files (>100MB) in the current directory"

# Code analysis
flourish agent "Review the code in src/ and suggest refactoring opportunities"

# Documentation
flourish agent "Generate a summary of all the functions in utils.py"
```

### Bash Integration

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Add flourish to PATH if installed locally
export PATH=$PATH:/path/to/flourish/.venv/bin

# Create convenient alias (optional)
alias ai='flourish'
```

Then you can use:
```bash
# Launch terminal interface
ai

# Or use CLI mode
ai agent "What is Kubernetes?"
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (see `env.example`):

```bash
API_KEY=your-api-key-here
MODEL=gpt-4o-mini
```

The `.env` file is automatically loaded when you run the application - no need to `source` it!

### Supported Models

Flourish uses [LiteLLM](https://litellm.ai/) for multi-provider support. You can use models from:

- **OpenAI**: `gpt-4o-mini`, `gpt-4`, `gpt-3.5-turbo`, etc.
- **Anthropic**: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, etc.
- **Google**: `gemini/gemini-2.0-flash`, `gemini/gemini-pro`, etc.
- **And many more** - see [LiteLLM documentation](https://docs.litellm.ai/docs/providers) for the full list

To use a different model, set the `MODEL` environment variable:
```bash
MODEL=anthropic/claude-3-opus-20240229
```

### Commands Configuration (Allowlist/Blacklist)

The allowlist and blacklist are managed in `config/commands.json`. This file is automatically created and updated by the agent.

```json
{
  "allowlist": [
    "ls",
    "git"
  ],
  "blacklist": [
    "rm",
    "dd"
  ]
}
```

You can manually edit this file, or use the agent's tools to manage it.

### Command History

Flourish automatically saves your command history across sessions:

- **History Location**: `~/.config/flourish/history`
- **History Features**:
  - Persistent across sessions (stored in `~/.config/flourish/history`)
  - Navigate with `↑/↓` arrow keys
  - Reverse search with `Ctrl+R` (fzf-like interface)
  - Case-insensitive search
  - In-memory history limited to 1000 entries per session

The history file is automatically created on first use and persists all your commands for easy access in future sessions.

## Development

### Prerequisites

- Python 3.10+ (3.12+ recommended)
- `pip` (Python package installer)
- `pre-commit` (for git hooks)

### Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
pytest
```

### Linting & Type Checking

```bash
ruff check .
black --check .
mypy flourish
```

### Formatting

```bash
black .
ruff format .
```

## Project Structure

```
flourish/
├── .github/              # GitHub Actions workflows
├── flourish/              # Main application source code
│   ├── agent/            # Agent definitions and logic
│   ├── completions/      # Command completion system
│   │   ├── git.py        # Git command completions
│   │   ├── loader.py     # Completion script loader
│   │   └── registry.py   # Completion registry
│   ├── config/           # Configuration management
│   ├── logging/          # Logging utilities
│   ├── plugins/          # Plugin system for extending capabilities
│   │   ├── base.py       # Plugin base classes
│   │   ├── cd_completer.py  # Enhanced cd completion
│   │   ├── enhancers.py  # Command output enhancers
│   │   └── zsh_bindings.py  # Example: zsh-like bindings
│   ├── runner/           # Agent execution logic
│   ├── tools/            # Custom tools for bash execution
│   └── ui/               # Text User Interface (TUI) and CLI
├── config/               # Persistent configuration files (e.g., commands.json)
├── docs/                 # Project documentation
│   ├── architecture.md   # System architecture
│   ├── plugins.md        # Plugin system guide
│   └── third-party-libraries.md
├── tests/                # Unit and integration tests
├── .env.example          # Example environment variables
├── pyproject.toml        # Project metadata and build configuration
├── README.md             # Project README
├── CHANGELOG.md          # Project changelog
├── CONTRIBUTING.md       # Contribution guidelines
├── SECURITY.md           # Security policy
└── LICENSE               # License file
```

## Extending Flourish

### Plugin System

Flourish includes a powerful plugin system that allows you to add custom commands, aliases, and behaviors. Create plugins to:

- Add command aliases (e.g., `ll` -> `ls -la`)
- Implement zsh-like features (e.g., `cd ...` to go back directories)
- Add custom shortcuts and workflows
- Extend terminal capabilities
- Enhance command output with colors and hints

See [docs/plugins.md](docs/plugins.md) for detailed documentation on creating plugins.

**Example**: The `ZshBindingsPlugin` adds zsh-like behaviors:
- `cd` (alone) → goes to home directory
- `cd ...` → goes back 2 directories
- `cd ....` → goes back 3 directories

### Completion System

Flourish includes a flexible completion system that supports:

- **Built-in completions**: Common commands like `cd` and `git` have enhanced completions
- **Custom completion scripts**: Create completion scripts for any command
- **Nested directory completion**: Smart path completion for `cd` with nested directory support

Completion scripts can be placed in:
- Project completions: `completions/` directory in the project root
- User completions: `~/.config/flourish/completions/`

See the completion system in `flourish/completions/` for examples.

## Security Considerations

- **Command Execution**: The agent mode can execute commands. Always review what the agent plans to do before confirming execution.
- **Allowlist/Blacklist**: Use allowlists in production environments to restrict command execution.
- **API Keys**: Never commit your `.env` file or API keys to version control.
- **Permissions**: The agent runs with the same permissions as your user account.

For detailed security information, see [SECURITY.md](SECURITY.md).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Powered by [LiteLLM](https://litellm.ai/) for seamless LLM integration
- Built with [Google ADK](https://github.com/google/generative-ai-python) for agent orchestration
- Terminal interface powered by [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)
- Syntax highlighting by [Pygments](https://pygments.org/)

## Roadmap

- [x] Interactive terminal environment
- [x] Config file for persistent settings (commands.json)
- [x] Plugin system for custom tools
- [x] Command completion system
- [ ] Better command validation and sandboxing
- [ ] Multi-agent orchestration
- [ ] Web UI option
- [ ] Additional completion scripts for more commands

## Support

- Issues: [GitHub Issues](https://github.com/made-after-dark/flourish/issues)
- Discussions: [GitHub Discussions](https://github.com/made-after-dark/flourish/discussions)
