# Third-Party Libraries Used in Flouri

This document outlines the key third-party libraries used in the Flouri project, their purpose, and licensing information.

## Core Dependencies

| Library | Purpose | License | Version |
|---------|---------|---------|---------|
| [google-adk](https://github.com/google/generative-ai-python) | Google AI Development Kit for agent orchestration | Apache-2.0 | >=1.22.0 |
| [LiteLLM](https://litellm.ai/) | Unified interface for multiple LLM providers (OpenAI, Anthropic, Google, etc.) | MIT | >=1.81.0 |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Load environment variables from `.env` files | BSD-3-Clause | >=1.0.0 |
| [pydantic](https://github.com/pydantic/pydantic) | Data validation using Python type annotations | MIT | >=2.5.0 |
| [pydantic-settings](https://github.com/pydantic/pydantic-settings) | Settings management using Pydantic models | MIT | >=2.1.0 |
| [click](https://github.com/pallets/click) | Command-line interface creation | BSD-3-Clause | >=8.1.0 |
| [rich](https://github.com/Textualize/rich) | Rich text and beautiful formatting in the terminal | MIT | >=13.7.0 |
| [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) | Interactive terminal interface with completion and history | BSD-3-Clause | >=3.0.0 |
| [pygments](https://pygments.org/) | Syntax highlighting library | BSD-2-Clause | >=2.15.0 |

## Development Dependencies

| Library | Purpose | License | Version |
|---------|---------|---------|---------|
| [pytest](https://github.com/pytest-dev/pytest) | Testing framework | MIT | >=7.4.0 |
| [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) | Pytest plugin for asyncio support | Apache-2.0 | >=0.21.0 |
| [pytest-cov](https://github.com/pytest-dev/pytest-cov) | Coverage plugin for pytest | MIT | >=4.1.0 |
| [black](https://github.com/psf/black) | Code formatter | MIT | >=23.11.0 |
| [ruff](https://github.com/astral-sh/ruff) | Fast Python linter and formatter | MIT | >=0.1.6 |
| [mypy](https://github.com/python/mypy) | Static type checker for Python | MIT | >=1.7.0 |
| [pre-commit](https://github.com/pre-commit/pre-commit) | Git hooks framework | MIT | >=3.5.0 |

## Key Libraries Explained

### Google ADK

**Purpose**: Google AI Development Kit provides the agent framework for orchestrating AI interactions, tool calling, session management, and streaming responses.

**Why it's used**: Google ADK provides a robust foundation for building agentic applications with support for tools, planning, and multi-turn conversations. It handles the complex orchestration between the LLM and the tools that Flouri provides.

**Documentation**: https://github.com/google/generative-ai-python

### LiteLLM

**Purpose**: LiteLLM provides a unified interface to interact with multiple LLM providers, including OpenAI, Anthropic, Google, and many others. This allows Flouri to support various models without provider-specific code.

**Why it's used**: Instead of being locked into a single provider, LiteLLM enables users to choose their preferred LLM provider by simply changing the `MODEL` environment variable. Google ADK uses LiteLLM as its model backend.

**Documentation**: https://docs.litellm.ai/

### Prompt-Toolkit

**Purpose**: Prompt-toolkit provides a powerful, cross-platform library for building interactive command-line applications with advanced features like auto-completion, syntax highlighting, and key bindings.

**Why it's used**: It provides the foundation for Flouri's TUI, enabling rich terminal interactions including command completion, history navigation, and syntax highlighting. It's more flexible than Textual for this use case as it provides lower-level control over terminal interactions.

**Documentation**: https://python-prompt-toolkit.readthedocs.io/

### Pygments

**Purpose**: Pygments is a syntax highlighting library that supports over 500 programming languages and markup formats.

**Why it's used**: Used in conjunction with prompt-toolkit to provide syntax highlighting for shell commands and code snippets in the terminal interface.

**Documentation**: https://pygments.org/

### Rich

**Purpose**: Rich provides beautiful terminal output with formatting, colors, tables, and markdown rendering.

**Why it's used**: Used for formatting AI responses, displaying markdown content, and creating visually appealing output in both the TUI and CLI modes.

**Documentation**: https://rich.readthedocs.io/

### Click

**Purpose**: Click is a Python package for creating command-line interfaces.

**Why it's used**: It provides a clean, declarative way to define CLI commands and options (like `flouri agent`), making the codebase more maintainable.

**Documentation**: https://click.palletsprojects.com/

### Pydantic

**Purpose**: Pydantic provides data validation using Python type annotations.

**Why it's used**: It ensures configuration data is validated and properly typed, reducing runtime errors.

**Documentation**: https://docs.pydantic.dev/

## License Compatibility

All dependencies use permissive licenses (MIT, BSD, Apache-2.0) that are compatible with the Apache License 2.0 used by Flouri.

## Updating Dependencies

Dependencies are managed in `pyproject.toml`. To update:

```bash
pip install --upgrade -e ".[dev]"
```

For production dependencies only:

```bash
pip install --upgrade -e .
```

## Security Considerations

- All dependencies are regularly updated to include security patches.
- Pre-commit hooks run security checks before commits.
- Dependencies are pinned to minimum versions to ensure compatibility while allowing security updates.
