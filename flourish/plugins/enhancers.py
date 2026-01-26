"""Command enhancement plugins for Flourish."""

import os
import stat
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class CommandEnhancer(ABC):
    """Base class for command enhancement plugins.

    Enhancers can intercept and modify command output, add features,
    or provide hints without completely replacing command execution.
    """

    @abstractmethod
    def name(self) -> str:
        """Return the enhancer name."""
        pass

    @abstractmethod
    def should_enhance(self, command: str) -> bool:
        """Check if this enhancer should enhance the given command.

        Args:
            command: The command string to check.

        Returns:
            True if this enhancer should enhance the command, False otherwise.
        """
        pass

    @abstractmethod
    def enhance_output(self, command: str, stdout: str, stderr: str, exit_code: int, cwd: str) -> dict[str, Any]:
        """Enhance command output.

        Args:
            command: The original command string.
            stdout: Standard output from the command.
            stderr: Standard error from the command.
            exit_code: Exit code of the command.
            cwd: Current working directory where command was executed.

        Returns:
            Dictionary with:
            - 'enhanced': bool - True if output was enhanced
            - 'stdout': str - Enhanced stdout (or original if not enhanced)
            - 'stderr': str - Enhanced stderr (or original if not enhanced)
            - 'hints': list[str] - Optional hints to display
        """
        pass


class LsColorEnhancer(CommandEnhancer):
    """Enhances ls output with color coding for files and directories."""

    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    # Colors
    BLUE = "\033[34m"  # Directories
    CYAN = "\033[36m"  # Symlinks
    GREEN = "\033[32m"  # Executables
    YELLOW = "\033[33m"  # Archives
    MAGENTA = "\033[35m"  # Images/media
    RED = "\033[31m"  # Errors

    def name(self) -> str:
        """Return the enhancer name."""
        return "ls_color"

    def should_enhance(self, command: str) -> bool:
        """Check if this enhancer should enhance ls commands."""
        cmd = command.strip()
        # Match ls, ls -l, ls -la, etc., but not lsblk, lsmod, etc.
        return cmd.startswith("ls ") or cmd == "ls"

    def _get_file_color(self, filepath: Path, cwd: Path) -> str:
        """Get color code for a file based on its type."""
        try:
            full_path = (cwd / filepath) if not filepath.is_absolute() else filepath

            if not full_path.exists():
                return self.RESET

            # Check if it's a symlink
            if full_path.is_symlink():
                return self.CYAN

            # Check file type
            if full_path.is_dir():
                return self.BLUE + self.BOLD
            elif full_path.is_file():
                # Check if executable
                if os.access(full_path, os.X_OK):
                    return self.GREEN
                # Check extension for common file types
                ext = full_path.suffix.lower()
                # Archives
                if ext in {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"}:
                    return self.YELLOW
                # Images/media
                if ext in {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".bmp",
                    ".svg",
                    ".mp4",
                    ".avi",
                    ".mkv",
                    ".mp3",
                    ".wav",
                }:
                    return self.MAGENTA
            return self.RESET
        except Exception:
            return self.RESET

    def enhance_output(self, command: str, stdout: str, stderr: str, exit_code: int, cwd: str) -> dict[str, Any]:
        """Add colors to ls output."""
        if exit_code != 0 or stderr:
            # Don't enhance if there's an error
            return {
                "enhanced": False,
                "stdout": stdout,
                "stderr": stderr,
                "hints": [],
            }

        # Check if it's ls -l format (long format)
        is_long_format = "-l" in command or "--long" in command or command.startswith("ll")

        # Parse ls output and add colors
        lines = stdout.split("\n")
        enhanced_lines = []

        for line in lines:
            if not line.strip():
                enhanced_lines.append(line)
                continue

            if is_long_format:
                # For ls -l format, color the filename (last part after date/time)
                # Format: permissions links owner group size date time name
                # Try to detect ls -l format: starts with file type char and has many fields
                parts = line.split()
                if len(parts) >= 9 and line[0] in ("d", "-", "l", "c", "b", "p", "s"):
                    # ls -l format detected
                    filename = " ".join(parts[8:])  # Handle filenames with spaces
                    filepath = Path(filename)
                    color = self._get_file_color(filepath, Path(cwd))
                    # Find where filename starts in the original line
                    filename_start = line.rfind(filename)
                    if filename_start != -1:
                        enhanced_line = line[:filename_start] + color + filename + self.RESET
                        enhanced_lines.append(enhanced_line)
                    else:
                        enhanced_lines.append(line)
                else:
                    # Not ls -l format, treat as regular
                    items = line.split()
                    colored_items = []
                    for item in items:
                        filepath = Path(item)
                        color = self._get_file_color(filepath, Path(cwd))
                        colored_items.append(color + item + self.RESET)
                    enhanced_lines.append("  ".join(colored_items))
            else:
                # Regular ls format - color each item
                items = line.split()
                colored_items = []
                for item in items:
                    # Skip ANSI codes if already present
                    if "\033[" in item:
                        colored_items.append(item)
                    else:
                        filepath = Path(item)
                        color = self._get_file_color(filepath, Path(cwd))
                        colored_items.append(color + item + self.RESET)
                # Preserve spacing (ls typically uses 2 spaces between items)
                enhanced_lines.append("  ".join(colored_items))

        enhanced_stdout = "\n".join(enhanced_lines)

        return {
            "enhanced": True,
            "stdout": enhanced_stdout,
            "stderr": stderr,
            "hints": [],
        }


class CdEnhancementPlugin(CommandEnhancer):
    """Enhances cd command with directory suggestions and hints."""

    def name(self) -> str:
        """Return the enhancer name."""
        return "cd_enhancement"

    def should_enhance(self, command: str) -> bool:
        """Check if this enhancer should enhance cd commands."""
        return command.strip().startswith("cd ")

    def enhance_output(self, command: str, stdout: str, stderr: str, exit_code: int, cwd: str) -> dict[str, Any]:
        """Provide hints for cd command."""
        hints = []

        if exit_code != 0 and stderr:
            # If cd failed, suggest similar directories
            target = command[3:].strip()
            if target:
                try:
                    current = Path(cwd)
                    # Look for similar directory names
                    if current.is_dir():
                        try:
                            dirs = [d for d in current.iterdir() if d.is_dir()]
                            # Find directories that start with the target
                            matches = [d.name for d in dirs if d.name.lower().startswith(target.lower())]
                            if matches:
                                hints.append(f"Did you mean: {', '.join(matches[:5])}?")
                        except PermissionError:
                            pass
                except Exception:
                    pass

        return {
            "enhanced": len(hints) > 0,
            "stdout": stdout,
            "stderr": stderr,
            "hints": hints,
        }


class EnhancerManager:
    """Manages command enhancer plugins."""

    def __init__(self):
        self.enhancers: list[CommandEnhancer] = []

    def register(self, enhancer: CommandEnhancer):
        """Register an enhancer.

        Args:
            enhancer: The enhancer to register.
        """
        self.enhancers.append(enhancer)

    def enhance(self, command: str, stdout: str, stderr: str, exit_code: int, cwd: str) -> dict[str, Any]:
        """Apply all relevant enhancers to command output.

        Args:
            command: The command string.
            stdout: Standard output from the command.
            stderr: Standard error from the command.
            exit_code: Exit code of the command.
            cwd: Current working directory.

        Returns:
            Dictionary with enhanced output, stderr, and hints.
        """
        enhanced_stdout = stdout
        enhanced_stderr = stderr
        all_hints = []

        for enhancer in self.enhancers:
            if enhancer.should_enhance(command):
                result = enhancer.enhance_output(command, enhanced_stdout, enhanced_stderr, exit_code, cwd)
                if result.get("enhanced", False):
                    enhanced_stdout = result.get("stdout", enhanced_stdout)
                    enhanced_stderr = result.get("stderr", enhanced_stderr)
                hints = result.get("hints", [])
                if hints:
                    all_hints.extend(hints)

        return {
            "stdout": enhanced_stdout,
            "stderr": enhanced_stderr,
            "hints": all_hints,
        }
