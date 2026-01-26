"""Completion loader for loading completion scripts."""

import importlib
import importlib.util
from pathlib import Path
from typing import Any

from prompt_toolkit.completion import Completion

from .registry import CompletionRegistry


class CompletionLoader:
    """Loads completion scripts from directories."""

    def __init__(self, registry: CompletionRegistry | None = None):
        """Initialize the completion loader.

        Args:
            registry: Optional completion registry. If None, creates a new one.
        """
        self.registry = registry or CompletionRegistry()
        self._loaded_modules: set[str] = set()

    def load_from_directory(self, directory: Path) -> int:
        """Load all completion scripts from a directory.

        Completion files should be named `<command>.py` or `_<command>.py`.
        Each file should define a `complete_<command>` function.

        Args:
            directory: Directory containing completion scripts

        Returns:
            Number of completion scripts loaded
        """
        if not directory.exists() or not directory.is_dir():
            return 0

        loaded_count = 0

        for file_path in directory.iterdir():
            if not file_path.is_file() or not file_path.suffix == ".py":
                continue

            if file_path.name.startswith("_"):
                continue  # Skip private files

            command_name = file_path.stem

            try:
                # Load the module
                spec = importlib.util.spec_from_file_location(
                    f"flourish_completion_{command_name}", file_path
                )
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for completion function
                completion_func_name = f"complete_{command_name}"
                if hasattr(module, completion_func_name):
                    completion_func = getattr(module, completion_func_name)
                    if callable(completion_func):
                        # Wrap the function to match our interface
                        def make_wrapper(cmd: str, func: Any) -> Any:
                            def wrapper(current_word: str, words: list[str], word_index: int) -> list[Completion]:
                                """Wrapper to convert completion function results."""
                                try:
                                    # Call the completion function
                                    # It should return a list of strings or Completions
                                    results = func(current_word, words, word_index)
                                    completions = []
                                    for result in results:
                                        if isinstance(result, Completion):
                                            completions.append(result)
                                        elif isinstance(result, str):
                                            # Convert string to Completion
                                            start_pos = -len(current_word) if current_word else 0
                                            completions.append(
                                                Completion(
                                                    result,
                                                    start_position=start_pos,
                                                    display=result,
                                                )
                                            )
                                    return completions
                                except Exception:
                                    return []

                            return wrapper

                        self.registry.register(
                            command_name,
                            make_wrapper(command_name, completion_func),
                            description=getattr(module, "__doc__", ""),
                        )
                        loaded_count += 1
                        self._loaded_modules.add(str(file_path))

            except Exception:
                # Skip files that fail to load
                continue

        return loaded_count

    def load_default_completions(self):
        """Load default completions from the completions directory."""
        # Load from project completions directory
        project_completions = Path(__file__).parent.parent.parent / "completions"
        if project_completions.exists():
            self.load_from_directory(project_completions)

        # Load from user completions directory
        user_completions = Path.home() / ".config" / "flourish" / "completions"
        if user_completions.exists():
            self.load_from_directory(user_completions)
