"""Text User Interface for bash.ai - Terminal chat interface."""

from rich.console import Console
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.events import Key
from textual.widgets import Footer, Header, Input, Markdown, Static

from ..config import get_settings
from ..config.config_manager import ConfigManager
from ..logging import initialize_session_log, log_conversation, log_session_end
from ..runner import run_agent, run_agent_live

console = Console()


class BashAIApp(App):
    """Main TUI application for bash.ai - Terminal chat interface."""

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

    .config-bar {
        background: $panel;
        padding: 1;
        border-bottom: solid $primary;
    }

    .messages {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    .message {
        margin: 1;
        padding: 1;
    }

    .user-message {
        background: $primary 20%;
        border-left: solid $primary;
    }

    .agent-message {
        background: $panel;
        border-left: solid $success;
    }

    .system-message {
        background: $warning 20%;
        border-left: solid $warning;
        text-style: italic;
    }

    .input-area {
        border-top: solid $primary;
        padding: 1;
        background: $surface;
    }

    #prompt-input {
        width: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear_messages", "Clear"),
        ("?", "show_help", "Help"),
        ("ctrl+a", "select_all", "Select All"),
        ("escape", "clear_input", "Clear Input"),
        ("ctrl+u", "clear_line", "Clear Line"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config_manager = ConfigManager()
        self.messages: list[dict[str, str]] = []
        self.current_allowlist = self.config_manager.get_allowlist()
        self.current_blacklist = self.config_manager.get_blacklist()
        self.command_history: list[str] = []
        self.history_index = -1

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Static("🤖 bash.ai - AI-Powered Bash Environment", classes="header")

        # Configuration bar
        yield Static(id="config-bar", classes="config-bar")

        # Messages area
        with VerticalScroll(id="messages-container", classes="messages"):
            yield Markdown(id="messages-display")

        # Input area
        with Container(classes="input-area"):
            yield Input(
                placeholder="Type your prompt or use /help for commands... (↑/↓ for history, Ctrl+U to clear)",
                id="prompt-input",
            )

        yield Footer()

    def on_mount(self):
        """Called when app starts."""
        # Initialize session log
        log_file = initialize_session_log()
        self.add_system_message(
            f"Welcome to bash.ai! Type /help for available commands. Session log: {log_file}"
        )

        self.update_config_bar()
        # Focus on prompt input
        self.query_one("#prompt-input", Input).focus()

    def update_config_bar(self):
        """Update the configuration bar."""
        try:
            settings = get_settings()
            api_key_status = "✓" if settings.api_key else "✗"
            model = settings.model
        except ValueError:
            api_key_status = "✗"
            model = "Not configured"

        allowlist_str = ", ".join(self.current_allowlist) if self.current_allowlist else "None"
        blacklist_str = ", ".join(self.current_blacklist) if self.current_blacklist else "None"

        config_text = (
            f"Model: {model} | "
            f"API: {api_key_status} | "
            f"Allowlist: {allowlist_str} | "
            f"Blacklist: {blacklist_str}"
        )
        self.query_one("#config-bar", Static).update(config_text)

    def add_message(self, content: str, message_type: str = "user"):
        """Add a message to the display."""
        self.messages.append({"content": content, "type": message_type})
        self.update_messages_display()

    def add_system_message(self, content: str):
        """Add a system message."""
        self.add_message(content, "system")

    def update_messages_display(self):
        """Update the messages display."""
        messages_md = []
        for msg in self.messages:
            if msg["type"] == "user":
                messages_md.append(f"**You:** {msg['content']}\n")
            elif msg["type"] == "agent":
                messages_md.append(f"{msg['content']}\n")
            else:  # system
                messages_md.append(f"*System:* {msg['content']}\n")

        self.query_one("#messages-display", Markdown).update("---\n".join(messages_md))

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        input_widget = event.input
        prompt = input_widget.value.strip()
        input_widget.value = ""
        self.history_index = -1  # Reset history index

        if not prompt:
            return

        # Add to command history (avoid duplicates)
        if self.command_history and self.command_history[-1] != prompt:
            self.command_history.append(prompt)
        elif not self.command_history:
            self.command_history.append(prompt)

        # Limit history size
        if len(self.command_history) > 100:
            self.command_history.pop(0)

        # Handle slash commands
        if prompt.startswith("/"):
            await self.handle_command(prompt)
        else:
            # Regular prompt - send to agent
            self.add_message(prompt, "user")
            log_conversation("user", prompt)
            await self.send_prompt(prompt)

    async def handle_command(self, command: str):
        """Handle slash commands."""
        parts = command.split(None, 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "/help":
            help_text = """
**Available Commands:**
- `/allow <command>` - Add command to allowlist
- `/remove-allow <command>` - Remove command from allowlist
- `/blacklist <command>` - Add command to blacklist
- `/remove-blacklist <command>` - Remove command from blacklist
- `/allowlist` - Show current allowlist
- `/blacklist` - Show current blacklist
- `/clear` - Clear message history
- `/help` - Show this help message
- `/config` - Show current configuration

**Keyboard Shortcuts:**
- `↑` / `↓` - Navigate command history
- `Ctrl+A` - Select all text (terminal dependent)
- `Ctrl+U` - Clear current line
- `Ctrl+K` - Clear from cursor to end of line
- `Ctrl+W` - Delete word before cursor
- `Escape` - Clear input field
- `Ctrl+L` - Clear message history
- `?` - Show help
- `Q` or `Ctrl+C` - Quit

**Usage:**
Just type your prompt normally (no prefix needed) to interact with the AI agent.
            """
            self.add_system_message(help_text.strip())

        elif cmd == "/allow":
            if args:
                self.config_manager.add_to_allowlist(args)
                self.current_allowlist = self.config_manager.get_allowlist()
                self.update_config_bar()
                self.add_system_message(f"✓ Added '{args}' to allowlist")
            else:
                self.add_system_message("✗ Usage: /allow <command>")

        elif cmd == "/remove-allow":
            if args:
                self.config_manager.remove_from_allowlist(args)
                self.current_allowlist = self.config_manager.get_allowlist()
                self.update_config_bar()
                self.add_system_message(f"✓ Removed '{args}' from allowlist")
            else:
                self.add_system_message("✗ Usage: /remove-allow <command>")

        elif cmd == "/blacklist":
            if args:
                self.config_manager.add_to_blacklist(args)
                self.current_blacklist = self.config_manager.get_blacklist()
                self.update_config_bar()
                self.add_system_message(f"✓ Added '{args}' to blacklist")
            else:
                self.add_system_message("✗ Usage: /blacklist <command>")

        elif cmd == "/remove-blacklist":
            if args:
                self.config_manager.remove_from_blacklist(args)
                self.current_blacklist = self.config_manager.get_blacklist()
                self.update_config_bar()
                self.add_system_message(f"✓ Removed '{args}' from blacklist")
            else:
                self.add_system_message("✗ Usage: /remove-blacklist <command>")

        elif cmd == "/allowlist":
            if self.current_allowlist:
                self.add_system_message(f"Allowlist: {', '.join(self.current_allowlist)}")
            else:
                self.add_system_message("Allowlist: None (all commands allowed)")

        elif cmd == "/blacklist":
            if self.current_blacklist:
                self.add_system_message(f"Blacklist: {', '.join(self.current_blacklist)}")
            else:
                self.add_system_message("Blacklist: None")

        elif cmd == "/clear":
            self.messages = []
            self.update_messages_display()
            self.add_system_message("Message history cleared")

        elif cmd == "/config":
            try:
                settings = get_settings()
                config_info = f"""
**Configuration:**
- Model: {settings.model}
- API Key: {'✓ Set' if settings.api_key else '✗ Not Set'}
- Config File: {self.config_manager.config_path}
- Allowlist: {', '.join(self.current_allowlist) if self.current_allowlist else 'None'}
- Blacklist: {', '.join(self.current_blacklist) if self.current_blacklist else 'None'}
                """
                self.add_system_message(config_info.strip())
            except ValueError as e:
                self.add_system_message(f"✗ Error loading config: {e}")

        else:
            self.add_system_message(f"✗ Unknown command: {cmd}. Type /help for available commands.")

    async def action_clear_messages(self):
        """Clear message history."""
        self.messages = []
        self.update_messages_display()
        self.add_system_message("Message history cleared")

    async def action_show_help(self):
        """Show help message."""
        await self.handle_command("/help")

    async def action_select_all(self):
        """Select all text in the input."""
        input_widget = self.query_one("#prompt-input", Input)
        input_widget.focus()
        # Note: Input widget selection is handled by the terminal

    async def action_clear_input(self):
        """Clear input field."""
        input_widget = self.query_one("#prompt-input", Input)
        input_widget.value = ""
        self.history_index = -1
        input_widget.focus()

    async def action_clear_line(self):
        """Clear current line (Ctrl+U)."""
        input_widget = self.query_one("#prompt-input", Input)
        input_widget.value = ""
        self.history_index = -1
        input_widget.focus()

    def on_key(self, event: Key) -> None:
        """Handle keyboard events for command history and shortcuts."""
        input_widget = self.query_one("#prompt-input", Input)

        # Only handle keys when input is focused
        if not input_widget.has_focus:
            return

        # Arrow up - previous command in history
        if event.key == "up":
            if self.command_history:
                if self.history_index == -1:
                    # Save current input if starting to navigate history
                    current_value = input_widget.value
                    if current_value and current_value not in self.command_history:
                        self.command_history.append(current_value)
                    self.history_index = len(self.command_history) - 1
                elif self.history_index > 0:
                    self.history_index -= 1

                if 0 <= self.history_index < len(self.command_history):
                    input_widget.value = self.command_history[self.history_index]
                    # Move cursor to end
                    input_widget.cursor_position = len(input_widget.value)
                event.prevent_default()

        # Arrow down - next command in history
        elif event.key == "down":
            if self.command_history and self.history_index >= 0:
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    input_widget.value = self.command_history[self.history_index]
                    input_widget.cursor_position = len(input_widget.value)
                else:
                    # Reached end of history, clear input
                    self.history_index = -1
                    input_widget.value = ""
                event.prevent_default()

        # Escape - Clear input
        elif event.key == "escape":
            input_widget.value = ""
            self.history_index = -1
            event.prevent_default()

        # Ctrl+K - Clear from cursor to end (Unix style)
        elif event.key == "ctrl+k":
            cursor_pos = input_widget.cursor_position
            input_widget.value = input_widget.value[:cursor_pos]
            input_widget.cursor_position = len(input_widget.value)
            event.prevent_default()

        # Ctrl+W - Delete word before cursor (Unix style)
        elif event.key == "ctrl+w":
            cursor_pos = input_widget.cursor_position
            text = input_widget.value
            # Find word boundary
            i = cursor_pos - 1
            while i >= 0 and text[i] == " ":
                i -= 1
            while i >= 0 and text[i] != " ":
                i -= 1
            new_text = text[: i + 1] + text[cursor_pos:]
            input_widget.value = new_text
            input_widget.cursor_position = i + 1
            event.prevent_default()

    async def send_prompt(self, prompt: str, stream: bool = False):
        """Send the prompt to the agent."""
        # Get current allowlist/blacklist from config
        allowlist = self.current_allowlist if self.current_allowlist else None
        blacklist = self.current_blacklist if self.current_blacklist else None

        # Show thinking indicator
        thinking_id = len(self.messages)
        self.messages.append(
            {"content": "[bold blue]Agent is thinking...[/bold blue]", "type": "agent"}
        )
        self.update_messages_display()

        try:
            if stream:
                # Streaming mode
                response_text = ""

                def stream_callback(text: str):
                    nonlocal response_text
                    response_text += text
                    # Update the last message
                    self.messages[thinking_id]["content"] = response_text
                    self.update_messages_display()

                response = await run_agent_live(
                    prompt,
                    allowed_commands=allowlist,
                    blacklisted_commands=blacklist,
                    stream_callback=stream_callback,
                )
                # Final update
                self.messages[thinking_id]["content"] = response
            else:
                # Standard mode
                response = await run_agent(
                    prompt,
                    allowed_commands=allowlist,
                    blacklisted_commands=blacklist,
                )
                self.messages[thinking_id]["content"] = response
                # Note: run_agent already logs the conversation

            self.update_messages_display()
        except Exception as e:
            self.messages[thinking_id]["content"] = f"[bold red]Error:[/bold red] {e}"
            self.update_messages_display()


def run_tui():
    """Run the TUI application."""
    try:
        app = BashAIApp()
        app.run()
    finally:
        # Log session end when TUI exits
        log_session_end()
