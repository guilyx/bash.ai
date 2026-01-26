# bash.ai

> AI-powered bash environment enhancement tool using LiteLLM

`bash.ai` is an open-source tool that enhances your bash environment with agentic AI capabilities. It allows you to interact with various LLMs directly from your terminal and execute complex workflows through AI orchestration.

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

- **Security Controls**: Allowlist and blacklist for AI-executed commands (when AI runs commands via tools)

## Prerequisites

- Python 3.12 or later
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
   git clone https://github.com/made-after-dark/bash.ai.git
   cd bash.ai
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   cp env.example .env
   # Edit .env and add your API_KEY
   ```

2. **Launch the terminal**:
   ```bash
   bash-ai
   ```

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
   git clone https://github.com/made-after-dark/bash.ai.git
   cd bash.ai
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

## Usage

### Terminal Interface (TUI) - Recommended

Launch the AI-enabled terminal environment:

```bash
bash-ai
# or
bash-ai tui
```

This opens an interactive terminal where you can:

1. **Execute commands directly** (just like a normal terminal):
   ```bash
   $ ls -la
   $ git status
   $ cd ~/projects
   $ pwd
   ```

2. **Get AI assistance** using the `?` prefix:
   ```bash
   $ ? explain the difference between git merge and rebase
   $ ? how do I check disk usage?
   $ ? help me write a script to find large files
   ```

3. **Use keyboard shortcuts**:
   - `Ctrl+A` - Start an AI prompt
   - `↑/↓` - Navigate command history
   - `Ctrl+L` - Clear screen
   - `?` - Show help
   - `Q` or `Ctrl+C` - Quit

### Command-Line Interface (CLI)

For non-interactive use or scripting:

```bash
# Ask questions
bash-ai agent "Explain how Docker containers work"

# With allowlist (only allow specific commands for AI execution)
bash-ai agent --allowlist "ls,cd,git,find" "Show me git status and list files"

# With blacklist (prevent specific commands)
bash-ai agent --blacklist "rm,dd,format" "Help me organize my project files"

# With live streaming (real-time output)
bash-ai agent --stream "Explain how Docker containers work"
bash-ai agent -s "List files and show git status"  # Short form
```

### Bash Integration

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Add bash-ai to PATH if installed locally
export PATH=$PATH:/path/to/bash.ai/.venv/bin

# Create convenient alias (optional)
alias ai='bash-ai'
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

`bash.ai` uses [LiteLLM](https://litellm.ai/) for multi-provider support. You can use models from:

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

## Development

### Prerequisites

- Python 3.12+
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
mypy bash_ai
```

### Formatting

```bash
black .
ruff format .
```

## Project Structure

```
bash.ai/
├── .github/              # GitHub Actions workflows
├── bash_ai/              # Main application source code
│   ├── agent/            # Agent definitions and logic
│   ├── config/           # Configuration management
│   ├── logging/          # Logging utilities
│   ├── plugins/          # Plugin system for extending capabilities
│   │   ├── base.py       # Plugin base classes
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

## Extending bash.ai

### Plugin System

bash.ai includes a powerful plugin system that allows you to add custom commands, aliases, and behaviors. Create plugins to:

- Add command aliases (e.g., `ll` -> `ls -la`)
- Implement zsh-like features (e.g., `cd ...` to go back directories)
- Add custom shortcuts and workflows
- Extend terminal capabilities

See [docs/plugins.md](docs/plugins.md) for detailed documentation on creating plugins.

**Example**: The `ZshBindingsPlugin` adds zsh-like behaviors:
- `cd` (alone) → goes to home directory
- `cd ...` → goes back 2 directories
- `cd ....` → goes back 3 directories

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
- Uses [Gemini](https://deepmind.google/technologies/gemini/) models (configurable)

## Roadmap

- [x] Interactive terminal environment
- [x] Config file for persistent settings (commands.json)
- [ ] Plugin system for custom tools
- [ ] Better command validation and sandboxing
- [ ] Multi-agent orchestration
- [ ] Web UI option
- [ ] Advanced bash completion integration

## Support

- Issues: [GitHub Issues](https://github.com/made-after-dark/bash.ai/issues)
- Discussions: [GitHub Discussions](https://github.com/made-after-dark/bash.ai/discussions)
