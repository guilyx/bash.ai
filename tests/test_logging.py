"""Tests for logging system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from flourish.logging import (
    get_session_dir,
    initialize_session_log,
    log_conversation,
    log_session_end,
    log_terminal_error,
    log_terminal_output,
    log_tool_call,
)


@pytest.fixture
def temp_logs_dir(tmp_path, monkeypatch):
    """Create a temporary logs directory."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)
    monkeypatch.setattr("flourish.logging.logger.BASE_LOGS_DIR", logs_dir)
    return logs_dir


def test_initialize_session_log(temp_logs_dir):
    """Test initializing session log."""
    session_dir = initialize_session_log()
    assert session_dir.exists()
    assert session_dir.is_dir()
    assert (session_dir / "conversation.log").exists()
    assert (session_dir / "terminal.log").exists()


def test_log_tool_call(temp_logs_dir):
    """Test logging a tool call."""
    initialize_session_log()
    log_tool_call("test_tool", {"param": "value"}, "result", success=True)

    session_dir = get_session_dir()
    assert session_dir is not None
    log_file = session_dir / "conversation.log"
    assert log_file.exists()

    # Check log content
    content = log_file.read_text()
    assert "test_tool" in content
    assert "tool_call" in content


def test_log_conversation(temp_logs_dir):
    """Test logging a conversation."""
    initialize_session_log()
    log_conversation("user", "Hello, AI!")

    session_dir = get_session_dir()
    log_file = session_dir / "conversation.log"
    content = log_file.read_text()
    assert "user" in content
    assert "Hello, AI!" in content


def test_log_terminal_output(temp_logs_dir):
    """Test logging terminal output."""
    initialize_session_log()
    log_terminal_output("ls -la", "file1.txt\nfile2.txt", "", 0, "/tmp")

    session_dir = get_session_dir()
    log_file = session_dir / "terminal.log"
    assert log_file.exists()

    content = log_file.read_text()
    assert "ls -la" in content
    assert "file1.txt" in content


def test_log_terminal_error(temp_logs_dir):
    """Test logging terminal error."""
    initialize_session_log()
    log_terminal_error("rm nonexistent", "No such file", "/tmp")

    session_dir = get_session_dir()
    log_file = session_dir / "terminal.log"
    content = log_file.read_text()
    assert "rm nonexistent" in content
    assert "error" in content


def test_log_session_end(temp_logs_dir):
    """Test logging session end."""
    initialize_session_log()
    log_session_end()

    session_dir = get_session_dir()
    log_file = session_dir / "conversation.log"
    content = log_file.read_text()
    assert "session_end" in content


def test_get_session_dir(temp_logs_dir):
    """Test getting session directory."""
    session_dir = initialize_session_log()
    retrieved_dir = get_session_dir()
    assert retrieved_dir == session_dir


def test_log_tool_call_truncation(temp_logs_dir):
    """Test that long tool call results are truncated."""
    initialize_session_log()
    long_result = "x" * 2000
    log_tool_call("test", {}, long_result, success=True)

    session_dir = get_session_dir()
    log_file = session_dir / "conversation.log"
    content = log_file.read_text()
    assert "[truncated]" in content


def test_log_conversation_truncation(temp_logs_dir):
    """Test that long conversation messages are truncated."""
    initialize_session_log()
    long_message = "x" * 3000
    log_conversation("user", long_message)

    session_dir = get_session_dir()
    log_file = session_dir / "conversation.log"
    content = log_file.read_text()
    assert "[truncated]" in content
