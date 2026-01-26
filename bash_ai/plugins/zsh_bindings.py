"""Zsh-like bindings plugin for bash.ai."""

import os
from pathlib import Path
from typing import Any

from .base import Plugin


class ZshBindingsPlugin(Plugin):
    """Plugin that provides zsh-like command bindings."""

    def name(self) -> str:
        """Return the plugin name."""
        return "zsh_bindings"

    def should_handle(self, command: str) -> bool:
        """Check if this plugin should handle the command."""
        cmd = command.strip()
        # Handle: cd (alone), cd with 3+ dots (..., ...., etc.)
        if cmd == "cd":
            return True
        if cmd.startswith("cd "):
            parts = cmd.split()
            if len(parts) == 2:
                path = parts[1]
                # Check if it's a dots pattern with 3+ dots
                clean_path = path.replace("/", "")
                if clean_path and all(c == "." for c in clean_path) and len(clean_path) >= 3:
                    return True
        return False

    async def execute(self, command: str, cwd: str) -> dict[str, Any]:
        """Execute zsh-like command bindings."""
        cmd = command.strip()
        parts = cmd.split()

        try:
            if cmd == "cd":
                # cd alone goes to home
                home = Path.home()
                os.chdir(str(home))
                return {
                    "handled": True,
                    "output": "",
                    "error": "",
                    "exit_code": 0,
                    "new_cwd": str(home),
                }

            elif len(parts) == 2 and parts[0] == "cd":
                path = parts[1]
                current = Path(cwd)

                # Check if it's a dots pattern (cd ... or cd ....)
                # Remove slashes and check if it's all dots
                clean_path = path.replace("/", "")
                if clean_path and all(c == "." for c in clean_path):
                    dot_count = len(clean_path)
                    if dot_count >= 3:  # cd ... or more
                        # Calculate how many directories to go back
                        # cd ... = 3 dots = go back 2 directories (dots - 1)
                        # cd .... = 4 dots = go back 3 directories
                        # cd ..... = 5 dots = go back 4 directories
                        go_back = dot_count - 1

                        # Go back the specified number of directories
                        target = current
                        for _ in range(go_back):
                            parent = target.parent
                            if parent == target:  # Reached root
                                break
                            target = parent

                        os.chdir(str(target))
                        return {
                            "handled": True,
                            "output": "",
                            "error": "",
                            "exit_code": 0,
                            "new_cwd": str(target),
                        }

            # Not handled by this plugin
            return {"handled": False}

        except Exception as e:
            return {
                "handled": True,
                "output": "",
                "error": str(e),
                "exit_code": 1,
            }
