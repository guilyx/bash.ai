"""Terminal User Interface for bash.ai - AI-enabled terminal environment."""

import asyncio
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import (
    Completer,
    Completion,
    FuzzyCompleter,
    PathCompleter,
    WordCompleter,
)
from prompt_toolkit.formatted_text import FormattedText, ANSI
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.search import SearchDirection
from prompt_toolkit.styles import Style
from pygments.lexers.shell import BashLexer
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

from ..config import get_settings
from ..config.config_manager import ConfigManager
from ..logging import (
    initialize_session_log,
    log_conversation,
    log_session_end,
    log_terminal_error,
    log_terminal_output,
)
from ..plugins import PluginManager, ZshBindingsPlugin
from ..plugins.cd_completer import CdCompleter
from ..plugins.enhancers import EnhancerManager, LsColorEnhancer, CdEnhancementPlugin
from ..runner import run_agent
from ..tools.tools import GLOBAL_CWD, set_allowlist_blacklist

# AI assistance trigger prefix
AI_PREFIX = "?"

# Common bash commands for auto-completion
BASH_COMMANDS = [
    "ls",
    "cd",
    "pwd",
    "cat",
    "grep",
    "find",
    "git",
    "docker",
    "python",
    "pip",
    "npm",
    "node",
    "echo",
    "mkdir",
    "rm",
    "cp",
    "mv",
    "chmod",
    "chown",
    "tar",
    "zip",
    "unzip",
    "curl",
    "wget",
    "ssh",
    "scp",
    "rsync",
    "ps",
    "kill",
    "top",
    "htop",
    "df",
    "du",
    "free",
    "history",
    "clear",
    "exit",
    "export",
    "env",
    "which",
    "whereis",
    "man",
    "help",
]


def get_git_branch(cwd: Path) -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            return f"({branch})" if branch else ""
    except Exception:
        pass
    return ""


def get_git_status(cwd: Path) -> str:
    """Get git status indicator."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            if result.stdout.strip():
                return "*"  # Has changes
            return "+"  # Clean
    except Exception:
        pass
    return ""


def format_prompt(cwd: Path):
    """Format the terminal prompt with git info using prompt_toolkit FormattedText."""
    try:
        home = Path.home()
        try:
            rel_path = cwd.relative_to(home)
            display_path = f"~/{rel_path}" if str(rel_path) != "." else "~"
        except ValueError:
            display_path = str(cwd)
    except Exception:
        display_path = str(cwd)

    git_branch = get_git_branch(cwd)
    git_status = get_git_status(cwd) if git_branch else ""

    # Build formatted text parts
    parts = []
    parts.append(("ansicyan", display_path))

    if git_branch:
        parts.append(("ansimagenta", git_branch))
        if git_status:
            parts.append(("ansiyellow", git_status))

    parts.append(("ansigreen", " $ "))

    return FormattedText(parts)


class BashCompleter(Completer):
    """Custom completer for bash commands with context-aware completion."""

    def __init__(self, cwd: Path | None = None):
        """Initialize the bash completer.

        Args:
            cwd: Current working directory for path completions.
        """
        self.cwd = cwd or Path.cwd()
        self.command_completer = FuzzyCompleter(WordCompleter(BASH_COMMANDS, ignore_case=True))
        self.path_completer = PathCompleter()
        self.cd_completer = CdCompleter(cwd=self.cwd)
        # Git subcommands
        self.git_commands = [
            "add",
            "commit",
            "push",
            "pull",
            "status",
            "log",
            "branch",
            "checkout",
            "merge",
            "rebase",
            "stash",
            "diff",
            "show",
            "reset",
            "revert",
            "clone",
            "init",
            "remote",
            "fetch",
        ]
        # Commands that take directory arguments
        self.directory_commands = {"cd", "ls", "mkdir", "rmdir", "find", "grep"}
        # Commands that take file arguments
        self.file_commands = {"cat", "less", "more", "head", "tail", "grep", "rm", "mv", "cp"}

    def _get_git_completions(self, document, complete_event):
        """Get git subcommand completions."""
        text = document.text_before_cursor
        parts = text.split()

        if len(parts) == 2 and parts[0] == "git":
            # Suggest git subcommands
            word = parts[1].lower()
            for cmd in self.git_commands:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word), display=cmd)

    def _is_command_complete(self, command: str) -> bool:
        """Check if a command string is a complete known command."""
        if not command:
            return False
        # Check if it's an exact match or ends with a space
        return command.strip() in BASH_COMMANDS or command.endswith(" ")

    def get_completions(self, document, complete_event):
        text_before = document.text_before_cursor
        text = text_before.strip()
        parts = text.split()

        # Handle git commands
        if parts and parts[0] == "git":
            if len(parts) == 1:
                # Just "git" - suggest git subcommands
                yield from self._get_git_completions(document, complete_event)
            elif len(parts) == 2:
                # "git <subcommand>" - suggest git subcommands
                yield from self._get_git_completions(document, complete_event)
            else:
                # "git <subcommand> <args>" - suggest paths/files
                yield from self.path_completer.get_completions(document, complete_event)
            return

        # Empty input - only show commands
        if not text:
            yield from self.command_completer.get_completions(document, complete_event)
            return

        # Check if text ends with space (indicates command is complete and expecting argument)
        ends_with_space = text_before.endswith(" ") or text_before.endswith("\t")

        # Single word (potentially incomplete command)
        if len(parts) == 1:
            if ends_with_space:
                # Command is complete (e.g., "cd "), show context-specific completions
                command = parts[0].lower()
                # Special handling for cd - use enhanced completer with nested directory support
                if command == "cd":
                    # Update cd completer's current directory
                    self.cd_completer.cwd = self.cwd
                    yield from self.cd_completer.get_completions(document, complete_event)
                elif command in self.directory_commands:
                    yield from self.path_completer.get_completions(document, complete_event)
                elif command in self.file_commands:
                    yield from self.path_completer.get_completions(document, complete_event)
                else:
                    # Generic fallback - suggest paths
                    yield from self.path_completer.get_completions(document, complete_event)
            else:
                # Incomplete command - only suggest commands
                yield from self.command_completer.get_completions(document, complete_event)
            return

        # Multiple words - first word is the command, show context-specific completions
        if len(parts) >= 2:
            command = parts[0].lower()
            # Special handling for cd - use enhanced completer with nested directory support
            if command == "cd":
                # Update cd completer's current directory
                self.cd_completer.cwd = self.cwd
                yield from self.cd_completer.get_completions(document, complete_event)
            # For other directory commands, suggest directories
            elif command in self.directory_commands:
                yield from self.path_completer.get_completions(document, complete_event)
            # For file commands, suggest files and directories
            elif command in self.file_commands:
                yield from self.path_completer.get_completions(document, complete_event)
            # For other commands, suggest paths (generic fallback)
            else:
                yield from self.path_completer.get_completions(document, complete_event)


class TerminalApp:
    """AI-enabled terminal environment using prompt_toolkit."""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.current_allowlist = self.config_manager.get_allowlist()
        self.current_blacklist = self.config_manager.get_blacklist()
        self.current_dir = Path.cwd()
        self.command_history: list[str] = []
        self.agent_task: asyncio.Task | None = None
        self.console = Console()

        # Set global allowlist/blacklist for tools
        set_allowlist_blacklist(
            allowlist=self.current_allowlist if self.current_allowlist else None,
            blacklist=self.current_blacklist if self.current_blacklist else None,
        )

        # Initialize session log
        initialize_session_log()

        # Setup plugin system
        self.plugin_manager = PluginManager()
        self.plugin_manager.register(ZshBindingsPlugin())

        # Setup command enhancer system
        self.enhancer_manager = EnhancerManager()
        self.enhancer_manager.register(LsColorEnhancer())
        self.enhancer_manager.register(CdEnhancementPlugin())

        # Setup prompt_toolkit
        self.completer = BashCompleter(cwd=self.current_dir)
        self.history = InMemoryHistory()

        # Try to load history from file
        history_file = Path.home() / ".config" / "bash.ai" / "history"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.history = FileHistory(str(history_file))
        except Exception:
            self.history = InMemoryHistory()

        # Create key bindings
        self.kb = KeyBindings()

        @self.kb.add("c-l")
        def clear_screen(event):
            """Clear screen."""
            event.app.output.write("\033[2J\033[H")

        @self.kb.add("c-r")
        def reverse_search(event):
            """Start reverse search (fzf-like)."""
            # This will be handled by prompt_toolkit's built-in reverse search
            pass

        # Create prompt session with enhanced features
        self.session = PromptSession(
            completer=self.completer,
            history=self.history,
            key_bindings=self.kb,
            lexer=PygmentsLexer(BashLexer),
            enable_history_search=True,  # Enable Ctrl+R for reverse search
            search_ignore_case=True,  # Case-insensitive search
            style=Style.from_dict(
                {
                    "completion-menu.completion": "bg:#008888 #ffffff",
                    "completion-menu.completion.current": "bg:#00aaaa #000000",
                    "scrollbar.background": "bg:#88aaaa",
                    "scrollbar.button": "bg:#222222",
                }
            ),
            complete_while_typing=True,  # Show completions while typing
            complete_in_thread=True,  # Don't block on completions
        )

    def print_welcome(self):
        """Print welcome message."""
        print("\033[36m" + "bash.ai - AI-Enabled Terminal Environment" + "\033[0m")
        print("\033[90m" + "Type commands directly, or use '?' prefix for AI assistance" + "\033[0m")
        print("\033[90m" + "Press Ctrl+D to exit" + "\033[0m")
        print()

    async def execute_command(self, cmd: str):
        """Execute a bash command."""
        global GLOBAL_CWD

        # Handle special built-in commands
        if cmd == "clear" or cmd == "cls":
            print("\033[2J\033[H", end="")
            return

        # Try plugins first
        plugin_result = await self.plugin_manager.execute(cmd, str(self.current_dir))
        if plugin_result and plugin_result.get("handled", False):
            # Plugin handled the command
            if plugin_result.get("error"):
                print(f"\033[91m{plugin_result['error']}\033[0m", file=__import__("sys").stderr)
            if plugin_result.get("output"):
                print(plugin_result["output"], end="")
            # Update directory if plugin changed it
            if "new_cwd" in plugin_result:
                self.current_dir = Path(plugin_result["new_cwd"])
                GLOBAL_CWD = str(self.current_dir)
                # Update completer's current directory
                self.completer.cwd = self.current_dir
                self.completer.cd_completer.cwd = self.current_dir
            return

        # Handle cd command (standard behavior)
        if cmd.startswith("cd "):
            new_path = cmd[3:].strip()
            if not new_path:
                new_path = str(Path.home())
            try:
                target = (self.current_dir / new_path).resolve()
                if target.is_dir():
                    self.current_dir = target
                    os.chdir(str(self.current_dir))
                    GLOBAL_CWD = str(self.current_dir)
                    # Update completer's current directory
                    self.completer.cwd = self.current_dir
                    self.completer.cd_completer.cwd = self.current_dir
                else:
                    print(f"\033[91mcd: {new_path}: No such file or directory\033[0m")
            except Exception as e:
                print(f"\033[91mcd: {str(e)}\033[0m")
            return

        # Execute command using subprocess
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                cwd=str(self.current_dir),
            )
            stdout, stderr = process.communicate()

            # Apply command enhancers
            enhanced = self.enhancer_manager.enhance(
                cmd, stdout, stderr, process.returncode, str(self.current_dir)
            )

            # Log terminal output (original, not enhanced)
            log_terminal_output(
                command=cmd,
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode,
                cwd=str(self.current_dir),
            )

            # Display enhanced output
            if enhanced["stdout"]:
                print(enhanced["stdout"], end="")
            if enhanced["stderr"]:
                print(enhanced["stderr"], end="", file=__import__("sys").stderr)
            # Display hints if any
            if enhanced.get("hints"):
                for hint in enhanced["hints"]:
                    print(f"\033[33m💡 {hint}\033[0m")

            # Update directory if command changed it
            try:
                new_cwd = Path.cwd()
                if new_cwd != self.current_dir:
                    self.current_dir = new_cwd
                    GLOBAL_CWD = str(self.current_dir)
                    # Update completer's current directory
                    self.completer.cwd = self.current_dir
                    self.completer.cd_completer.cwd = self.current_dir
            except Exception:
                pass

        except Exception as e:
            error_msg = f"\033[91mError executing command: {e}\033[0m"
            print(error_msg, file=__import__("sys").stderr)
            log_terminal_error(command=cmd, error=str(e), cwd=str(self.current_dir))

    def _format_response(self, response: str):
        """Format AI response with proper code block rendering."""
        # Check if response contains code blocks
        code_block_pattern = r"```(\w+)?\n?(.*?)```"

        # Find all code blocks
        matches = list(re.finditer(code_block_pattern, response, re.DOTALL))

        if not matches:
            # No code blocks, just print as markdown
            self.console.print(Markdown(response))
            return

        # Process response with code blocks
        last_end = 0
        for match in matches:
            # Print text before code block
            if match.start() > last_end:
                text_before = response[last_end:match.start()].strip()
                if text_before:
                    self.console.print(Markdown(text_before))

            # Extract language and code
            language = match.group(1) or "text"
            code = match.group(2).strip()

            # Print code block with syntax highlighting
            # Use a terminal-friendly theme
            syntax = Syntax(
                code,
                language,
                theme="one-dark",
                line_numbers=False,
                word_wrap=True,
            )
            self.console.print(syntax)

            last_end = match.end()

        # Print remaining text after last code block
        if last_end < len(response):
            text_after = response[last_end:].strip()
            if text_after:
                self.console.print(Markdown(text_after))

    async def handle_ai_request(self, prompt: str):
        """Handle an AI assistance request."""
        self.console.print("[cyan]🤖 AI is thinking...[/cyan]")

        # Get current allowlist/blacklist
        allowlist = self.current_allowlist if self.current_allowlist else None
        blacklist = self.current_blacklist if self.current_blacklist else None

        # Log user request
        log_conversation("user", prompt)

        try:
            # Run agent
            response = await run_agent(
                prompt,
                allowed_commands=allowlist,
                blacklisted_commands=blacklist,
            )

            # Display AI response with formatting
            self.console.print("[cyan]🤖[/cyan]", end=" ")
            self._format_response(response)

        except Exception as e:
            self.console.print(f"[red]❌ AI Error: {e}[/red]")

    async def run(self):
        """Run the terminal application."""
        self.print_welcome()

        try:
            while True:
                try:
                    # Get command from user
                    command = await self.session.prompt_async(format_prompt(self.current_dir))

                    if not command.strip():
                        continue

                    # Add to command history
                    if self.command_history and self.command_history[-1] != command:
                        self.command_history.append(command)
                    elif not self.command_history:
                        self.command_history.append(command)

                    # Limit history size
                    if len(self.command_history) > 1000:
                        self.command_history.pop(0)

                    # Check if it's an AI request
                    if command.startswith(AI_PREFIX):
                        # Remove prefix and send to AI
                        ai_prompt = command[1:].strip()
                        if ai_prompt:
                            await self.handle_ai_request(ai_prompt)
                        else:
                            print("\033[91mUsage: ? <your question>\033[0m")
                    else:
                        # Regular bash command
                        await self.execute_command(command)

                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    print("^C")
                    continue
                except EOFError:
                    # Handle Ctrl+D
                    print("\n\033[90mExiting...\033[0m")
                    break

        finally:
            log_session_end()


def run_tui():
    """Run the terminal TUI application."""
    app = TerminalApp()
    asyncio.run(app.run())
