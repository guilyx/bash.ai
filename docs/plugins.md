# Plugin System

The bash.ai plugin system allows you to extend the terminal environment with custom commands, aliases, and behaviors. This document explains how the plugin system works and how to create your own plugins.

## Overview

Plugins are checked **before** standard command execution. If a plugin handles a command, it executes and returns a result. If no plugin handles it, the command falls through to standard bash execution.

## Plugin Architecture

### Base Classes

All plugins inherit from the `Plugin` base class and must implement three methods:

1. **`name()`** - Returns a unique plugin identifier
2. **`should_handle(command)`** - Determines if the plugin should handle a command
3. **`execute(command, cwd)`** - Executes the command and returns a result

### Plugin Manager

The `PluginManager` manages registered plugins and tries them in order when a command is executed.

## Creating a Plugin

### Step 1: Create Your Plugin Class

Create a new file in `bash_ai/plugins/` (e.g., `my_plugin.py`):

```python
"""My custom plugin for bash.ai."""

from pathlib import Path
from typing import Any

from .base import Plugin


class MyPlugin(Plugin):
    """Description of what your plugin does."""

    def name(self) -> str:
        """Return the plugin name."""
        return "my_plugin"

    def should_handle(self, command: str) -> bool:
        """Check if this plugin should handle the command."""
        # Return True if your plugin should handle this command
        return command.strip().startswith("mycommand")

    async def execute(self, command: str, cwd: str) -> dict[str, Any]:
        """Execute the command."""
        try:
            # Your plugin logic here
            result = "Plugin output"
            
            return {
                "handled": True,      # Must be True if plugin handled the command
                "output": result,     # Standard output (optional)
                "error": "",          # Error message if failed (optional)
                "exit_code": 0,       # Exit code (0 = success, non-zero = error)
                "new_cwd": cwd,       # New working directory if changed (optional)
            }
        except Exception as e:
            return {
                "handled": True,
                "output": "",
                "error": str(e),
                "exit_code": 1,
            }
```

### Step 2: Register Your Plugin

Add your plugin to the plugin manager in `bash_ai/ui/tui.py`:

```python
from ..plugins import PluginManager, ZshBindingsPlugin, MyPlugin

# In TerminalApp.__init__:
self.plugin_manager = PluginManager()
self.plugin_manager.register(ZshBindingsPlugin())
self.plugin_manager.register(MyPlugin())  # Add your plugin
```

### Step 3: Export Your Plugin

Add your plugin to `bash_ai/plugins/__init__.py`:

```python
from .my_plugin import MyPlugin

__all__ = ["Plugin", "PluginManager", "ZshBindingsPlugin", "MyPlugin"]
```

## Example: Zsh Bindings Plugin

The `ZshBindingsPlugin` demonstrates how to create a plugin:

```python
class ZshBindingsPlugin(Plugin):
    """Plugin that provides zsh-like command bindings."""

    def name(self) -> str:
        return "zsh_bindings"

    def should_handle(self, command: str) -> bool:
        cmd = command.strip()
        # Handle: cd (alone), cd with 3+ dots
        if cmd == "cd":
            return True
        if cmd.startswith("cd "):
            parts = cmd.split()
            if len(parts) == 2:
                path = parts[1]
                clean_path = path.replace("/", "")
                if clean_path and all(c == "." for c in clean_path) and len(clean_path) >= 3:
                    return True
        return False

    async def execute(self, command: str, cwd: str) -> dict[str, Any]:
        # Implementation handles:
        # - cd (alone) -> home directory
        # - cd ... (3+ dots) -> go back (dots - 1) directories
        ...
```

## Plugin Return Values

Your plugin's `execute()` method must return a dictionary with these keys:

- **`handled`** (bool, required): `True` if the plugin handled the command, `False` to pass to next handler
- **`output`** (str, optional): Standard output to display
- **`error`** (str, optional): Error message if execution failed
- **`exit_code`** (int, optional): Exit code (0 = success, non-zero = error)
- **`new_cwd`** (str, optional): New working directory if the plugin changed it

## Plugin Ideas

Here are some ideas for plugins you could create:

### 1. Alias Plugin
Create command aliases (e.g., `ll` -> `ls -la`, `gst` -> `git status`)

### 2. Directory Bookmarks Plugin
Save and jump to bookmarked directories (e.g., `bookmark add work ~/projects/work`, `bookmark go work`)

### 3. History Search Plugin
Enhanced history search with fzf-like functionality

### 4. Git Shortcuts Plugin
Short git commands (e.g., `gst` -> `git status`, `gco` -> `git checkout`)

### 5. Environment Variable Plugin
Quick environment variable management

### 6. Project Switcher Plugin
Quickly switch between projects with custom commands

## Best Practices

1. **Be Specific**: Make `should_handle()` as specific as possible to avoid conflicts
2. **Error Handling**: Always wrap execution in try/except and return proper error responses
3. **Documentation**: Add clear docstrings explaining what your plugin does
4. **Testing**: Test your plugin with various inputs and edge cases
5. **Performance**: Keep plugin execution fast - plugins are checked on every command
6. **Directory Changes**: If your plugin changes directories, return `new_cwd` in the result

## Contributing Plugins

We welcome plugin contributions! To contribute a plugin:

1. **Create your plugin** following the structure above
2. **Add tests** for your plugin (if applicable)
3. **Update documentation** (this file or create a new section)
4. **Submit a PR** with:
   - Your plugin code
   - Tests (if applicable)
   - Documentation
   - Example usage

### Plugin Contribution Checklist

- [ ] Plugin follows the `Plugin` base class interface
- [ ] `should_handle()` is specific and efficient
- [ ] `execute()` handles errors gracefully
- [ ] Plugin is registered in `bash_ai/ui/tui.py`
- [ ] Plugin is exported in `bash_ai/plugins/__init__.py`
- [ ] Documentation added/updated
- [ ] Code follows project style (black, ruff)
- [ ] No breaking changes to existing functionality

## Advanced: Plugin Configuration

Plugins can access configuration through the `ConfigManager`:

```python
from ..config.config_manager import ConfigManager

class MyPlugin(Plugin):
    def __init__(self):
        self.config = ConfigManager()
        # Access config as needed
```

## Plugin Execution Order

Plugins are executed in the order they are registered. The first plugin that returns `handled: True` wins. Make sure your plugin's `should_handle()` is specific enough to avoid conflicts.

## Examples

### Example 1: Simple Alias Plugin

```python
class AliasPlugin(Plugin):
    """Plugin that provides command aliases."""

    def __init__(self):
        self.aliases = {
            "ll": "ls -la",
            "la": "ls -a",
            "gst": "git status",
            "gco": "git checkout",
        }

    def name(self) -> str:
        return "alias"

    def should_handle(self, command: str) -> bool:
        cmd = command.strip().split()[0] if command.strip() else ""
        return cmd in self.aliases

    async def execute(self, command: str, cwd: str) -> dict[str, Any]:
        cmd = command.strip().split()[0]
        alias_cmd = self.aliases[cmd]
        # Execute the aliased command
        # (In real implementation, you'd execute it via subprocess)
        return {
            "handled": True,
            "output": f"Alias: {cmd} -> {alias_cmd}",
            "exit_code": 0,
        }
```

### Example 2: Directory Navigation Plugin

```python
class QuickNavPlugin(Plugin):
    """Plugin for quick directory navigation."""

    def name(self) -> str:
        return "quick_nav"

    def should_handle(self, command: str) -> bool:
        return command.strip().startswith("goto ")

    async def execute(self, command: str, cwd: str) -> dict[str, Any]:
        parts = command.strip().split()
        if len(parts) != 2:
            return {"handled": False}
        
        target = parts[1]
        # Your navigation logic here
        # ...
        return {
            "handled": True,
            "output": f"Navigated to {target}",
            "exit_code": 0,
            "new_cwd": str(target_path),
        }
```

## Questions?

- Check existing plugins in `bash_ai/plugins/` for examples
- Open a [Discussion](https://github.com/made-after-dark/bash.ai/discussions) for questions
- Review [CONTRIBUTING.md](../CONTRIBUTING.md) for general contribution guidelines

Happy plugin development! 🚀
