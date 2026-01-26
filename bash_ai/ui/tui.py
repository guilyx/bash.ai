"""Terminal User Interface for bash.ai - AI-enabled terminal environment."""

import asyncio
import os
import subprocess
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.events import Key
from textual.widgets import Footer, Header, Input, Static

from ..config import get_settings
from ..config.config_manager import ConfigManager
from ..logging import (
    initialize_session_log,
    log_conversation,
    log_session_end,
    log_terminal_error,
    log_terminal_output,
)
from ..runner import run_agent
from ..tools.tools import GLOBAL_CWD, execute_bash, set_allowlist_blacklist

# AI assistance trigger prefix
AI_PREFIX = "?"


class TerminalApp(App):
    """AI-enabled terminal environment."""

    CSS = """
    Screen {
        background: $surface;
    }

    .header {
        text-align: center;
        padding: 1;
        background: $primary;
        color: $text;
        text-style: bold;
    }

    .terminal-output {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        background: rgb(0, 0, 0);
        color: rgb(200, 200, 200);
    }

    .terminal-line {
        margin: 0;
        padding: 0;
    }

    .command-line {
        color: rgb(100, 200, 100);
    }

    .output-line {
        color: rgb(200, 200, 200);
    }

    .error-line {
        color: rgb(255, 100, 100);
    }

    .ai-line {
        color: rgb(150, 200, 255);
    }

    .prompt-line {
        color: rgb(100, 150, 255);
    }

    .input-area {
        border-top: solid $primary;
        padding: 0 1;
        background: rgb(20, 20, 20);
    }

    #prompt-display {
        width: auto;
        padding-right: 1;
    }

    #command-input {
        width: 1fr;
        background: rgb(20, 20, 20);
        color: rgb(200, 200, 200);
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear_screen", "Clear"),
        ("ctrl+a", "ask_ai", "Ask AI"),
        ("?", "help", "Help"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config_manager = ConfigManager()
        self.current_allowlist = self.config_manager.get_allowlist()
        self.current_blacklist = self.config_manager.get_blacklist()
        self.command_history: list[str] = []
        self.history_index = -1
        self.output_lines: list[tuple[str, str]] = []  # (content, class)
        self.current_dir = Path.cwd()
        self.agent_task: asyncio.Task | None = None

        # Set global allowlist/blacklist for tools
        set_allowlist_blacklist(
            allowlist=self.current_allowlist if self.current_allowlist else None,
            blacklist=self.current_blacklist if self.current_blacklist else None,
        )

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Static("🤖 bash.ai - AI-Enabled Terminal", classes="header")

        # Terminal output area
        with VerticalScroll(id="terminal-output", classes="terminal-output"):
            yield Static(id="terminal-content")

        # Input area with prompt
        with Container(classes="input-area"):
            with Horizontal():
                yield Static(id="prompt-display")
                yield Input(
                    placeholder="",
                    id="command-input",
                )

        yield Footer()

    def on_mount(self):
        """Called when app starts."""
        # Initialize session log
        initialize_session_log()
        self.add_output_line("bash.ai - AI-Enabled Terminal Environment", "prompt-line")
        self.add_output_line("Type commands directly, or use '?' prefix for AI assistance", "prompt-line")
        self.add_output_line("Press Ctrl+A to ask AI, Ctrl+L to clear, ? for help", "prompt-line")
        self.add_output_line("", "output-line")
        self.update_prompt()
        self.query_one("#command-input", Input).focus()

    def update_prompt(self):
        """Update the prompt display with current directory."""
        try:
            # Get relative path from home or absolute if shorter
            home = Path.home()
            try:
                rel_path = self.current_dir.relative_to(home)
                display_path = f"~/{rel_path}" if str(rel_path) != "." else "~"
            except ValueError:
                display_path = str(self.current_dir)

            prompt = f"[{display_path}] $ "
            self.query_one("#prompt-display", Static).update(prompt)
        except Exception:
            self.query_one("#prompt-display", Static).update("$ ")

    def add_output_line(self, content: str, css_class: str = "output-line"):
        """Add a line to the terminal output."""
        self.output_lines.append((content, css_class))
        self.update_terminal_display()

    def update_terminal_display(self):
        """Update the terminal content display."""
        # Map CSS classes to Rich markup colors
        color_map = {
            "command-line": "[green]",
            "output-line": "[white]",
            "error-line": "[red]",
            "ai-line": "[cyan]",
            "prompt-line": "[blue]",
        }

        lines = []
        for content, css_class in self.output_lines:
            if content:
                # Use Rich markup for colors
                color_tag = color_map.get(css_class, "[white]")
                # Escape brackets in content to avoid Rich markup conflicts
                escaped_content = content.replace("[", "\\[").replace("]", "\\]")
                lines.append(f"{color_tag}{escaped_content}[/]")
            else:
                lines.append("")  # Empty line

        content = "\n".join(lines)
        self.query_one("#terminal-content", Static).update(content)
        # Scroll to bottom
        terminal_output = self.query_one("#terminal-output", VerticalScroll)
        terminal_output.scroll_end(animate=False)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input submission."""
        input_widget = event.input
        command = input_widget.value.strip()
        input_widget.value = ""
        self.history_index = -1

        if not command:
            return

        # Add to command history
        if self.command_history and self.command_history[-1] != command:
            self.command_history.append(command)
        elif not self.command_history:
            self.command_history.append(command)

        # Limit history size
        if len(self.command_history) > 1000:
            self.command_history.pop(0)

        # Show the command that was entered
        self.add_output_line(f"[{self._get_display_path()}] $ {command}", "command-line")

        # Check if it's an AI request
        if command.startswith(AI_PREFIX):
            # Remove prefix and send to AI
            ai_prompt = command[1:].strip()
            if ai_prompt:
                await self.handle_ai_request(ai_prompt)
            else:
                self.add_output_line("Usage: ? <your question>", "error-line")
        else:
            # Regular bash command
            await self.execute_command(command)

        # Update prompt and refocus input
        self.update_prompt()
        self.query_one("#command-input", Input).focus()

    def _get_display_path(self) -> str:
        """Get display path for prompt."""
        try:
            home = Path.home()
            try:
                rel_path = self.current_dir.relative_to(home)
                return f"~/{rel_path}" if str(rel_path) != "." else "~"
            except ValueError:
                return str(self.current_dir)
        except Exception:
            return str(self.current_dir)

    async def execute_command(self, cmd: str):
        """Execute a bash command."""
        global GLOBAL_CWD

        # Handle special built-in commands
        if cmd == "clear" or cmd == "cls":
            self.output_lines = []
            self.update_terminal_display()
            return

        if cmd.startswith("cd "):
            new_path = cmd[3:].strip()
            if not new_path:
                new_path = str(Path.home())
            try:
                target = (self.current_dir / new_path).resolve()
                if target.is_dir():
                    self.current_dir = target
                    os.chdir(str(self.current_dir))
                    # Update global CWD in tools
                    GLOBAL_CWD = str(self.current_dir)
                else:
                    self.add_output_line(f"cd: {new_path}: No such file or directory", "error-line")
            except Exception as e:
                self.add_output_line(f"cd: {str(e)}", "error-line")
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

            # Log terminal output
            log_terminal_output(
                command=cmd,
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode,
                cwd=str(self.current_dir),
            )

            # Display output
            if stdout:
                for line in stdout.rstrip().split("\n"):
                    self.add_output_line(line, "output-line")
            if stderr:
                for line in stderr.rstrip().split("\n"):
                    self.add_output_line(line, "error-line")

            # Update directory if command changed it (e.g., cd in subshell)
            try:
                new_cwd = Path.cwd()
                if new_cwd != self.current_dir:
                    self.current_dir = new_cwd
                    GLOBAL_CWD = str(self.current_dir)
            except Exception:
                pass

        except Exception as e:
            error_msg = f"Error executing command: {e}"
            self.add_output_line(error_msg, "error-line")
            log_terminal_error(command=cmd, error=str(e), cwd=str(self.current_dir))

    async def handle_ai_request(self, prompt: str):
        """Handle an AI assistance request."""
        self.add_output_line("🤖 AI is thinking...", "ai-line")

        # Get current allowlist/blacklist
        allowlist = self.current_allowlist if self.current_allowlist else None
        blacklist = self.current_blacklist if self.current_blacklist else None

        # Log user request
        log_conversation("user", prompt)

        try:
            # Run agent in background
            response = await run_agent(
                prompt,
                allowed_commands=allowlist,
                blacklisted_commands=blacklist,
            )

            # Remove thinking line and add response
            if self.output_lines and self.output_lines[-1][0] == "🤖 AI is thinking...":
                self.output_lines.pop()

            # Display AI response
            for line in response.split("\n"):
                if line.strip():
                    self.add_output_line(f"🤖 {line}", "ai-line")
                else:
                    self.add_output_line("", "ai-line")

        except Exception as e:
            # Remove thinking line
            if self.output_lines and self.output_lines[-1][0] == "🤖 AI is thinking...":
                self.output_lines.pop()
            error_msg = f"❌ AI Error: {e}"
            self.add_output_line(error_msg, "error-line")

    def on_key(self, event: Key) -> None:
        """Handle keyboard events."""
        input_widget = self.query_one("#command-input", Input)

        if not input_widget.has_focus:
            return

        # Arrow up - previous command
        if event.key == "up":
            if self.command_history:
                if self.history_index == -1:
                    current_value = input_widget.value
                    if current_value and current_value not in self.command_history:
                        self.command_history.append(current_value)
                    self.history_index = len(self.command_history) - 1
                elif self.history_index > 0:
                    self.history_index -= 1

                if 0 <= self.history_index < len(self.command_history):
                    input_widget.value = self.command_history[self.history_index]
                    input_widget.cursor_position = len(input_widget.value)
                event.prevent_default()

        # Arrow down - next command
        elif event.key == "down":
            if self.command_history and self.history_index >= 0:
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    input_widget.value = self.command_history[self.history_index]
                    input_widget.cursor_position = len(input_widget.value)
                else:
                    self.history_index = -1
                    input_widget.value = ""
                event.prevent_default()

        # Ctrl+L - Clear screen
        elif event.key == "ctrl+l":
            self.output_lines = []
            self.update_terminal_display()
            event.prevent_default()

    async def action_clear_screen(self):
        """Clear the terminal screen."""
        self.output_lines = []
        self.update_terminal_display()

    async def action_ask_ai(self):
        """Trigger AI assistance prompt."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.value = f"{AI_PREFIX} "
        input_widget.cursor_position = len(input_widget.value)
        input_widget.focus()

    async def action_help(self):
        """Show help message."""
        help_text = """
bash.ai - AI-Enabled Terminal

USAGE:
  - Type commands directly to execute them (e.g., 'ls', 'pwd', 'git status')
  - Use '?' prefix for AI assistance (e.g., '? explain git merge')
  - Press Ctrl+A to start an AI prompt

KEYBOARD SHORTCUTS:
  - ↑/↓        Navigate command history
  - Ctrl+L     Clear screen
  - Ctrl+A     Ask AI
  - ?          Show this help
  - Q/Ctrl+C   Quit

EXAMPLES:
  $ ls -la
  $ ? how do I check disk usage?
  $ git status
  $ ? explain the difference between merge and rebase
        """
        for line in help_text.strip().split("\n"):
            self.add_output_line(line, "prompt-line")

    async def action_quit(self):
        """Quit the application."""
        log_session_end()
        self.exit()


def run_tui():
    """Run the terminal TUI application."""
    app = TerminalApp()
    app.run()
