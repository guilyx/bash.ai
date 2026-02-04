"""Completion registry for managing command completions."""

from collections.abc import Callable

from prompt_toolkit.completion import Completion


class CompletionFunction:
    """Represents a completion function for a command."""

    def __init__(
        self,
        command: str,
        func: Callable[[str, list[str], int], list[Completion]],
        description: str = "",
    ):
        """Initialize a completion function.

        Args:
            command: The command name this completion handles
            func: Completion function that takes (word, words, word_index) and returns list of Completions
            description: Optional description of what this completion does
        """
        self.command = command
        self.func = func
        self.description = description


class CompletionRegistry:
    """Registry for managing command completion functions."""

    def __init__(self):
        """Initialize the completion registry."""
        self._completions: dict[str, CompletionFunction] = {}
        self._aliases: dict[str, str] = {}  # Maps alias to command

    def register(
        self,
        command: str,
        func: Callable[[str, list[str], int], list[Completion]],
        description: str = "",
    ):
        """Register a completion function for a command.

        Args:
            command: The command name (e.g., "git", "docker")
            func: Completion function that takes (current_word, all_words, word_index) and returns list of Completions
            description: Optional description
        """
        self._completions[command] = CompletionFunction(command, func, description)

    def register_alias(self, alias: str, command: str):
        """Register an alias for a command.

        Args:
            alias: The alias name
            command: The command it aliases to
        """
        self._aliases[alias] = command

    def get_completion(self, command: str) -> CompletionFunction | None:
        """Get completion function for a command.

        Args:
            command: The command name

        Returns:
            CompletionFunction if found, None otherwise
        """
        # Check direct match
        if command in self._completions:
            return self._completions[command]

        # Check aliases
        if command in self._aliases:
            aliased_command = self._aliases[command]
            if aliased_command in self._completions:
                return self._completions[aliased_command]

        return None

    def has_completion(self, command: str) -> bool:
        """Check if a completion exists for a command.

        Args:
            command: The command name

        Returns:
            True if completion exists, False otherwise
        """
        return self.get_completion(command) is not None

    def list_commands(self) -> list[str]:
        """List all commands with registered completions.

        Returns:
            List of command names
        """
        return list(self._completions.keys())
