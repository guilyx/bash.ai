"""CLI interface for Flourish."""

import sys

import click
from rich.console import Console
from rich.markdown import Markdown

from ..runner import run_agent_live_sync, run_agent_sync
from .tui import run_tui

console = Console()
error_console = Console(file=sys.stderr, style="bold red")


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx):
    """Flourish - AI-powered terminal environment (flouri.sh).

    Run without arguments to launch the TUI, or use subcommands for CLI mode.
    """
    # If no subcommand, launch TUI
    if ctx.invoked_subcommand is None:
        run_tui()


@cli.command(name="agent")
@click.argument("prompt", required=True)
@click.option(
    "--allowlist",
    "-a",
    help="Comma-separated list of allowed commands (e.g., 'ls,cd,git')",
    default=None,
)
@click.option(
    "--blacklist",
    "-b",
    help="Comma-separated list of blacklisted commands (e.g., 'rm,dd')",
    default=None,
)
@click.option(
    "--stream",
    "-s",
    is_flag=True,
    help="Enable live streaming output (real-time text streaming)",
    default=False,
)
def agent_command(prompt: str, allowlist: str | None, blacklist: str | None, stream: bool):
    """Run agent in CLI mode (non-interactive).

    Example:
        flourish agent "What is the difference between git merge and rebase?"
        flourish agent "List all files in the current directory"
        flourish agent -a "ls,cd,git" "Check git status"
        flourish agent -b "rm,dd" "Help me organize files"
        flourish agent --stream "Explain Docker containers"  # Live streaming output
    """
    try:
        # Parse allowlist and blacklist
        allowed_commands = (
            [cmd.strip() for cmd in allowlist.split(",") if cmd.strip()] if allowlist else None
        )
        blacklisted_commands = (
            [cmd.strip() for cmd in blacklist.split(",") if cmd.strip()] if blacklist else None
        )

        if stream:
            # Live streaming mode
            console.print("[bold blue]Agent is working (streaming)...[/bold blue]\n")

            def stream_callback(text: str):
                """Callback for streaming text chunks."""
                console.print(text, end="", markup=False)

            response = run_agent_live_sync(
                prompt,
                allowed_commands=allowed_commands,
                blacklisted_commands=blacklisted_commands,
                stream_callback=stream_callback,
            )
            console.print()  # New line after streaming
        else:
            # Standard mode
            console.print("[bold blue]Agent is working...[/bold blue]")
            response = run_agent_sync(
                prompt,
                allowed_commands=allowed_commands,
                blacklisted_commands=blacklisted_commands,
            )
            console.print(Markdown(response))
    except Exception as e:
        error_console.print(f"Error: {e}")
        sys.exit(1)


@cli.command()
def tui():
    """Launch the Text User Interface (default when run without arguments)."""
    run_tui()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
