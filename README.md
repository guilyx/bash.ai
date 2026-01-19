# bash.ai

> AI-powered bash environment enhancement tool using LiteLLM

`bash.ai` is an open-source tool that enhances your bash environment with agentic AI capabilities. It allows you to interact with various LLMs directly from your terminal and execute complex workflows through AI orchestration.

## Features

- **Unified Agent**: Single intelligent agent that can both answer questions and execute commands
  ```bash
  bash-ai "What is the difference between git merge and rebase?"
  bash-ai "List all files in the current directory and show git status"
  ```

- **Intelligent Execution**: The agent automatically determines when to execute code based on your request

- **Security Controls**: Allowlist and blacklist for command execution
  ```bash
  bash-ai --allowlist "ls,cd,git" "Check git status"
  bash-ai --blacklist "rm,dd" "Help me organize files"
  ```

- **AI-Enhanced Bash**: Auto-completion suggestions and intelligent command assistance

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

### Basic Usage

**Ask questions or request actions:**
```bash
# The agent will answer questions
bash-ai "Explain how Docker containers work"

# The agent will execute commands when needed
bash-ai "Find all .py files in the current directory"

# The agent intelligently decides when to execute code
bash-ai "What files are in this directory?"  # May execute ls
bash-ai "What is git?"  # Will just explain
```

### Advanced Usage

**With allowlist (only allow specific commands):**
```bash
bash-ai --allowlist "ls,cd,git,find" "Show me git status and list files"
```

**With blacklist (prevent specific commands):**
```bash
bash-ai --blacklist "rm,dd,format" "Help me organize my project files"
```

**With live streaming (real-time output):**
```bash
bash-ai --stream "Explain how Docker containers work"
bash-ai -s "List files and show git status"  # Short form
```

**Note**: For best streaming experience, use a live model in your `.env`:
```bash
GEMINI_MODEL=gemini-2.0-flash-live-001
```

**Specify a different model:**
```bash
# Set in .env file
GEMINI_MODEL=gemini-3-pro-preview
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
ai "What is Kubernetes?"
ai "Check my git status and show recent commits"
```

### AI-Enhanced Bash Features

The tool provides intelligent command suggestions and auto-completion:

- **Context-aware suggestions**: Based on your current directory and recent commands
- **Error recovery**: Suggests fixes when commands fail
- **Workflow automation**: Helps orchestrate complex multi-step tasks

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
│   ├── runner/           # Agent execution logic
│   ├── tools/            # Custom tools for bash execution
│   └── ui/               # Text User Interface (TUI) and CLI
├── config/               # Persistent configuration files (e.g., commands.json)
├── docs/                 # Project documentation (architecture, libraries, etc.)
├── tests/                # Unit and integration tests
├── .env.example          # Example environment variables
├── pyproject.toml        # Project metadata and build configuration
├── README.md             # Project README
├── CHANGELOG.md          # Project changelog
├── CONTRIBUTING.md       # Contribution guidelines
├── SECURITY.md           # Security policy
└── LICENSE               # License file
```

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

- [ ] Interactive mode with conversation history
- [ ] Config file for persistent settings
- [ ] Plugin system for custom tools
- [ ] Better command validation and sandboxing
- [ ] Multi-agent orchestration
- [ ] Web UI option
- [ ] Advanced bash completion integration

## Support

- Issues: [GitHub Issues](https://github.com/made-after-dark/bash.ai/issues)
- Discussions: [GitHub Discussions](https://github.com/made-after-dark/bash.ai/discussions)
