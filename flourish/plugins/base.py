"""Base plugin system for Flourish."""

from abc import ABC, abstractmethod
from typing import Any


class Plugin(ABC):
    """Base class for Flourish plugins."""

    @abstractmethod
    def name(self) -> str:
        """Return the plugin name."""
        pass

    @abstractmethod
    def should_handle(self, command: str) -> bool:
        """Check if this plugin should handle the given command.

        Args:
            command: The command string to check.

        Returns:
            True if this plugin should handle the command, False otherwise.
        """
        pass

    @abstractmethod
    async def execute(self, command: str, cwd: str) -> dict[str, Any]:
        """Execute the command.

        Args:
            command: The command string to execute.
            cwd: Current working directory.

        Returns:
            Dictionary with 'handled' (bool), 'output' (str), 'error' (str), 'exit_code' (int).
            If 'handled' is False, the command will be passed to the next handler.
        """
        pass


class PluginManager:
    """Manages plugins for command execution."""

    def __init__(self):
        self.plugins: list[Plugin] = []

    def register(self, plugin: Plugin):
        """Register a plugin.

        Args:
            plugin: The plugin to register.
        """
        self.plugins.append(plugin)

    async def execute(self, command: str, cwd: str) -> dict[str, Any] | None:
        """Try to execute a command using registered plugins.

        Args:
            command: The command string to execute.
            cwd: Current working directory.

        Returns:
            Dictionary with execution result if handled by a plugin, None otherwise.
        """
        for plugin in self.plugins:
            if plugin.should_handle(command):
                result = await plugin.execute(command, cwd)
                if result.get("handled", False):
                    return result
        return None
