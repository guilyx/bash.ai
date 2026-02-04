"""Unit tests for CLI (agent command, tui command)."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from flouri.ui.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_agent_command_standard_mode(runner):
    """agent command calls run_agent_sync and prints response."""
    with patch("flouri.ui.cli.run_agent_sync", return_value="**Done**"):
        result = runner.invoke(cli, ["agent", "list files"])
    assert result.exit_code == 0
    assert "Done" in result.output or "**" in result.output


def test_agent_command_with_allowlist_blacklist(runner):
    """agent command parses --allowlist and --blacklist."""
    with patch("flouri.ui.cli.run_agent_sync", return_value="ok") as mock_run:
        runner.invoke(cli, ["agent", "-a", "ls, pwd", "-b", " rm ", "hello"])
    mock_run.assert_called_once()
    call_kw = mock_run.call_args[1]
    assert call_kw["allowed_commands"] == ["ls", "pwd"]
    assert call_kw["blacklisted_commands"] == ["rm"]


def test_agent_command_stream_mode(runner):
    """agent command with --stream calls run_agent_live_sync."""
    with patch("flouri.ui.cli.run_agent_live_sync", return_value="streamed") as mock_run:
        result = runner.invoke(cli, ["agent", "--stream", "hello"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    assert mock_run.call_args[1]["stream_callback"] is not None


def test_agent_command_exception_exits_one(runner):
    """agent command exits 1 when run_agent_sync raises."""
    with patch("flouri.ui.cli.run_agent_sync", side_effect=RuntimeError("API error")):
        result = runner.invoke(cli, ["agent", "fail"])
    assert result.exit_code == 1


def test_tui_command_calls_run_tui(runner):
    """tui subcommand calls run_tui."""
    with patch("flouri.ui.cli.run_tui") as mock_tui:
        result = runner.invoke(cli, ["tui"])
    mock_tui.assert_called_once()
    assert result.exit_code == 0


def test_cli_no_subcommand_invokes_run_tui(runner):
    """Invoking cli with no subcommand calls run_tui (default)."""
    with patch("flouri.ui.cli.run_tui") as mock_tui:
        runner.invoke(cli, [])
    mock_tui.assert_called_once()


def test_agent_command_stream_callback_invoked(runner):
    """In stream mode, run_agent_live_sync receives a callback; invoking it covers console.print."""

    def call_stream_callback(
        prompt, allowed_commands=None, blacklisted_commands=None, stream_callback=None
    ):
        if stream_callback:
            stream_callback("chunk1")
            stream_callback("chunk2")
        return "done"

    with patch("flouri.ui.cli.run_agent_live_sync", side_effect=call_stream_callback):
        result = runner.invoke(cli, ["agent", "--stream", "hello"])
    assert result.exit_code == 0
    assert "chunk1" in result.output and "chunk2" in result.output
