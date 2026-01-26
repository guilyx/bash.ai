"""Enhanced cd completion plugin with nested directory structure support."""

import os
from pathlib import Path
from typing import Any

from prompt_toolkit.completion import Completion, Completer


class CdCompleter(Completer):
    """Enhanced completer for cd command with nested directory structure support."""

    def __init__(self, cwd: Path | None = None):
        """Initialize the cd completer.

        Args:
            cwd: Current working directory. If None, uses current directory.
        """
        self.cwd = cwd or Path.cwd()

    def _get_directories(self, base_path: Path, pattern: str = "") -> list[Path]:
        """Get directories matching the pattern, including nested ones.

        Args:
            base_path: Base path to search from.
            pattern: Pattern to match (can be partial path).

        Returns:
            List of matching directory paths.
        """
        directories = []
        try:
            if not base_path.exists() or not base_path.is_dir():
                return directories

            # If pattern is empty, return all immediate subdirectories
            if not pattern:
                try:
                    if not base_path.exists() or not base_path.is_dir():
                        return directories
                    for item in base_path.iterdir():
                        if item.is_dir() and not item.name.startswith("."):
                            directories.append(item)
                except (PermissionError, OSError):
                    pass
                return sorted(directories, key=lambda p: p.name.lower())

            # Parse the pattern - could be relative path like "dev/proj"
            pattern_parts = pattern.split("/")
            search_path = base_path

            # Navigate through the pattern path
            for i, part in enumerate(pattern_parts[:-1]):
                if not part:
                    continue
                # Try to find matching directory
                try:
                    for item in search_path.iterdir():
                        if item.is_dir() and item.name.startswith(part):
                            search_path = item
                            break
                    else:
                        # No match found, return empty
                        return directories
                except (PermissionError, OSError):
                    return directories

            # Now search in the final directory for the last part
            last_part = pattern_parts[-1]
            try:
                for item in search_path.iterdir():
                    if item.is_dir():
                        # Match if name starts with last_part or if last_part is empty
                        if not last_part or item.name.lower().startswith(last_part.lower()):
                            directories.append(item)
            except (PermissionError, OSError):
                pass

            return sorted(directories, key=lambda p: p.name.lower())

        except Exception:
            return directories

    def _format_completion(self, path: Path, base_path: Path, pattern: str) -> tuple[str, str]:
        """Format completion text and display.

        Args:
            path: The directory path to complete.
            base_path: Base path for relative display.
            pattern: The pattern being matched.

        Returns:
            Tuple of (completion_text, display_text).
        """
        try:
            # Get relative path from base
            try:
                rel_path = path.relative_to(base_path)
            except ValueError:
                rel_path = path

            # Completion text is just the directory name (or remaining path if nested)
            if "/" in pattern:
                # If we're completing a nested path, we need to provide the full remaining path
                pattern_parts = [p for p in pattern.split("/") if p]
                if pattern_parts:
                    # Find where we are in the path
                    rel_parts = list(rel_path.parts)
                    # Skip parts that match the pattern
                    start_idx = len(pattern_parts) - 1
                    if start_idx < len(rel_parts):
                        remaining_parts = rel_parts[start_idx:]
                        completion_text = "/".join(remaining_parts) if remaining_parts else path.name
                    else:
                        completion_text = path.name
                else:
                    completion_text = path.name
            else:
                completion_text = path.name

            # Display with depth indicator
            depth = len(rel_path.parts) - 1
            indent = "  " * depth if depth > 0 else ""
            display_text = f"{indent}{path.name}/"

            return completion_text, display_text

        except Exception:
            return path.name, path.name

    def get_completions(self, document, complete_event):
        """Get completions for cd command with nested directory support."""
        text_before = document.text_before_cursor
        text = text_before.strip()

        # Extract the path part after "cd " or "cd"
        if not text.startswith("cd"):
            return

        # Handle both "cd " and "cd" (without space)
        if text.startswith("cd "):
            path_part = text[3:].strip()
        elif text == "cd":
            # Just "cd" - show all directories
            path_part = ""
        else:
            # "cd" followed by something (like "cddev")
            return

        # Determine base path
        if path_part.startswith("/"):
            # Absolute path
            base_path = Path("/")
            search_pattern = path_part.lstrip("/")
        elif path_part.startswith("~"):
            # Home directory
            base_path = Path.home()
            search_pattern = path_part[1:].lstrip("/")
        else:
            # Relative path
            base_path = self.cwd
            search_pattern = path_part

        # Get matching directories
        directories = self._get_directories(base_path, search_pattern)

        # Calculate start position for completion
        # We need to find where the last part of the path starts
        if path_part:
            if "/" in path_part:
                # Find the last part after the last slash
                last_slash_pos = path_part.rfind("/")
                last_part = path_part[last_slash_pos + 1 :]
                start_position = -len(last_part) if last_part else 0
            else:
                start_position = -len(path_part)
        else:
            start_position = 0

        # Yield completions - use default style which will be styled by prompt_toolkit
        for directory in directories:
            completion_text, display_text = self._format_completion(directory, base_path, search_pattern)
            # Don't set style - let prompt_toolkit use its default completion menu styling
            yield Completion(
                completion_text,
                start_position=start_position,
                display=display_text,
            )
