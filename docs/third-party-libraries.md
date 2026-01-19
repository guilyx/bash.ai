# Third-Party Libraries Used in bash.ai

This document outlines the key third-party libraries used in the `bash.ai` project, their purpose, and licensing information.

## Core Dependencies

| Library | Purpose | License | Version |
|---------|---------|---------|---------|
| [LiteLLM](https://litellm.ai/) | Unified interface for multiple LLM providers (OpenAI, Anthropic, Google, etc.) | MIT | >=1.40.0 |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Load environment variables from `.env` files | BSD-3-Clause | >=1.0.0 |
| [pydantic](https://github.com/pydantic/pydantic) | Data validation using Python type annotations | MIT | >=2.5.0 |
| [pydantic-settings](https://github.com/pydantic/pydantic-settings) | Settings management using Pydantic models | MIT | >=2.1.0 |
| [click](https://github.com/pallets/click) | Command-line interface creation | BSD-3-Clause | >=8.1.0 |
| [rich](https://github.com/Textualize/rich) | Rich text and beautiful formatting in the terminal | MIT | >=13.7.0 |
| [textual](https://github.com/Textualize/textual) | Text User Interface (TUI) framework | MIT | >=0.60.0 |

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

### LiteLLM

**Purpose**: LiteLLM provides a unified interface to interact with multiple LLM providers, including OpenAI, Anthropic, Google, and many others. This allows `bash.ai` to support various models without provider-specific code.

**Why it's used**: Instead of being locked into a single provider (like Google ADK), LiteLLM enables users to choose their preferred LLM provider by simply changing the `MODEL` environment variable.

**Documentation**: https://docs.litellm.ai/

### Rich & Textual

**Purpose**: These libraries provide beautiful terminal output and interactive Text User Interfaces (TUIs).

- **Rich**: Handles formatting, colors, tables, and markdown rendering in the terminal.
- **Textual**: Builds on Rich to create interactive, event-driven TUIs.

**Why they're used**: They provide a modern, developer-friendly interface that's both functional and visually appealing.

**Documentation**:
- Rich: https://rich.readthedocs.io/
- Textual: https://textual.textualize.io/

### Click

**Purpose**: Click is a Python package for creating command-line interfaces.

**Why it's used**: It provides a clean, declarative way to define CLI commands and options, making the codebase more maintainable.

**Documentation**: https://click.palletsprojects.com/

### Pydantic

**Purpose**: Pydantic provides data validation using Python type annotations.

**Why it's used**: It ensures configuration data is validated and properly typed, reducing runtime errors.

**Documentation**: https://docs.pydantic.dev/

## License Compatibility

All dependencies use permissive licenses (MIT, BSD, Apache-2.0) that are compatible with the Apache License 2.0 used by `bash.ai`.

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
