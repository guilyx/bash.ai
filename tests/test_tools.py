"""Tests for tools module."""

import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from flourish.tools import (
    add_to_allowlist,
    add_to_blacklist,
    execute_bash,
    get_bash_tools,
    get_current_datetime,
    get_user,
    is_in_allowlist,
    is_in_blacklist,
    list_allowlist,
    list_blacklist,
    read_bash_history,
    read_conversation_history,
    remove_from_allowlist,
    remove_from_blacklist,
    set_allowlist_blacklist,
    set_cwd,
)


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for tests."""
    config_file = tmp_path / "config.json"
    # Write default config
    import json

    config_file.write_text(
        json.dumps({"allowlist": [], "blacklist": ["rm", "dd", "format", "mkfs"]}, indent=2)
    )
    return str(config_file)


@pytest.fixture
def mock_config_manager(temp_config_file):
    """Mock ConfigManager to use temporary config file."""
    with patch("flourish.config.config_manager.ConfigManager") as mock_class:
        from flourish.config.config_manager import ConfigManager

        # Create a real ConfigManager with temp file
        def create_manager(*args, **kwargs):
            return ConfigManager(config_file=temp_config_file)

        mock_class.side_effect = create_manager
        yield mock_class


@pytest.fixture
def mock_bash_config_manager(temp_config_file):
    """Mock ConfigManager in bash tools to use temporary config file."""
    with patch("flourish.config.config_manager.ConfigManager") as mock_class:
        from flourish.config.config_manager import ConfigManager

        # Create a real ConfigManager with temp file
        def create_manager(*args, **kwargs):
            return ConfigManager(config_file=temp_config_file)

        mock_class.side_effect = create_manager
        yield mock_class


@pytest.fixture
def reset_globals():
    """Reset global variables before each test."""
    import flourish.tools.globals as globals_module
    from flourish.tools.globals import (
        GLOBAL_ALLOWLIST,
        GLOBAL_BLACKLIST,
        GLOBAL_CWD,
    )

    # Save original values
    original_allowlist = GLOBAL_ALLOWLIST
    original_blacklist = GLOBAL_BLACKLIST
    original_cwd = GLOBAL_CWD

    # Reset to defaults
    globals_module.GLOBAL_ALLOWLIST = None
    globals_module.GLOBAL_BLACKLIST = None
    globals_module.GLOBAL_CWD = str(Path.cwd())

    yield

    # Restore original values
    globals_module.GLOBAL_ALLOWLIST = original_allowlist
    globals_module.GLOBAL_BLACKLIST = original_blacklist
    globals_module.GLOBAL_CWD = original_cwd


def test_set_cwd(tmp_path, reset_globals):
    """Test setting current working directory."""
    result = set_cwd(str(tmp_path))
    assert "Working directory set to" in result
    import flourish.tools.globals as globals_module

    assert globals_module.GLOBAL_CWD == str(tmp_path)


def test_set_cwd_invalid(reset_globals):
    """Test setting invalid directory."""
    with pytest.raises(ValueError):
        set_cwd("/nonexistent/path/12345")


def test_get_user(reset_globals):
    """Test getting user information."""
    result = get_user()
    assert "username" in result
    assert "home_directory" in result
    assert "current_working_directory" in result


def test_set_allowlist_blacklist(reset_globals):
    """Test setting allowlist and blacklist."""
    set_allowlist_blacklist(allowlist=["ls", "cd"], blacklist=["rm"])
    import flourish.tools.globals as globals_module

    assert "ls" in globals_module.GLOBAL_ALLOWLIST
    assert "rm" in globals_module.GLOBAL_BLACKLIST


def test_execute_bash_simple(reset_globals):
    """Test executing a simple bash command."""
    set_allowlist_blacklist(allowlist=["echo"], blacklist=None)
    result = execute_bash("echo hello", tool_context=None)
    assert result["status"] == "success"
    assert "hello" in result["stdout"]


def test_execute_bash_blacklisted(reset_globals):
    """Test that blacklisted commands are blocked."""
    set_allowlist_blacklist(allowlist=None, blacklist=["rm"])
    result = execute_bash("rm file.txt", tool_context=None)
    assert result["status"] == "blocked"
    assert "blacklisted" in result["message"].lower()


def test_execute_bash_not_in_allowlist(reset_globals, mock_bash_config_manager):
    """Test that commands not in allowlist are still executed (auto-added)."""
    set_allowlist_blacklist(allowlist=["ls"], blacklist=None)
    result = execute_bash("echo test", tool_context=None)
    # Command should be auto-added to allowlist and executed
    assert result["status"] == "success"


def test_add_to_allowlist(reset_globals, mock_config_manager):
    """Test adding command to allowlist."""
    set_allowlist_blacklist(allowlist=[], blacklist=None)
    result = add_to_allowlist("ls", tool_context=None)
    assert result["status"] == "success"
    import flourish.tools.globals as globals_module

    assert "ls" in globals_module.GLOBAL_ALLOWLIST


def test_add_to_blacklist(reset_globals, mock_config_manager):
    """Test adding command to blacklist."""
    set_allowlist_blacklist(allowlist=None, blacklist=[])
    result = add_to_blacklist("rm", tool_context=None)
    assert result["status"] == "success"
    import flourish.tools.globals as globals_module

    assert "rm" in globals_module.GLOBAL_BLACKLIST


def test_remove_from_allowlist(reset_globals, mock_config_manager):
    """Test removing command from allowlist."""
    set_allowlist_blacklist(allowlist=["ls"], blacklist=None)
    result = remove_from_allowlist("ls", tool_context=None)
    assert result["status"] == "success"
    import flourish.tools.globals as globals_module

    assert "ls" not in globals_module.GLOBAL_ALLOWLIST


def test_remove_from_blacklist(reset_globals, mock_config_manager):
    """Test removing command from blacklist."""
    set_allowlist_blacklist(allowlist=None, blacklist=["rm"])
    result = remove_from_blacklist("rm", tool_context=None)
    assert result["status"] == "success"
    import flourish.tools.globals as globals_module

    assert "rm" not in globals_module.GLOBAL_BLACKLIST


def test_get_bash_tools(reset_globals):
    """Test getting bash tools."""
    tools = get_bash_tools(allowlist=["ls"], blacklist=["rm"])
    assert len(tools) > 0
    # Check that tools are callable
    assert all(callable(tool) or hasattr(tool, "func") for tool in tools)


def test_execute_bash_error_handling(reset_globals):
    """Test error handling in execute_bash."""
    set_allowlist_blacklist(allowlist=["nonexistentcommand"], blacklist=None)
    result = execute_bash("nonexistentcommand12345", tool_context=None)
    # Should handle error gracefully
    assert "status" in result


def test_list_allowlist(reset_globals):
    """Test listing allowlist."""
    set_allowlist_blacklist(allowlist=["ls", "cd"], blacklist=None)
    result = list_allowlist()
    assert result["status"] == "success"
    assert "ls" in result["allowlist"]
    assert "cd" in result["allowlist"]
    assert result["count"] == 2


def test_list_blacklist(reset_globals):
    """Test listing blacklist."""
    set_allowlist_blacklist(allowlist=None, blacklist=["rm", "dd"])
    result = list_blacklist()
    assert result["status"] == "success"
    assert "rm" in result["blacklist"]
    assert "dd" in result["blacklist"]
    assert result["count"] == 2


def test_is_in_allowlist(reset_globals):
    """Test checking if command is in allowlist."""
    set_allowlist_blacklist(allowlist=["ls"], blacklist=None)
    result = is_in_allowlist("ls")
    assert result["status"] == "success"
    assert result["in_allowlist"] is True

    result = is_in_allowlist("cd")
    assert result["in_allowlist"] is False


def test_is_in_blacklist(reset_globals):
    """Test checking if command is in blacklist."""
    set_allowlist_blacklist(allowlist=None, blacklist=["rm"])
    result = is_in_blacklist("rm")
    assert result["status"] == "success"
    assert result["in_blacklist"] is True

    result = is_in_blacklist("ls")
    assert result["in_blacklist"] is False


def test_read_bash_history_nonexistent(tmp_path, monkeypatch):
    """Test reading bash history when file doesn't exist."""
    # Create the config directory structure but no history file
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_bash_history()
    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["entries"] == []
    assert "does not exist" in result["message"]


def test_read_bash_history_empty_file(tmp_path, monkeypatch):
    """Test reading bash history from empty file."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.touch()

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_bash_history()
    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["entries"] == []


def test_read_bash_history_with_commands(tmp_path, monkeypatch):
    """Test reading bash history with commands."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # Write some history entries (one per line, as prompt-toolkit format)
    history_file.write_text("ls -la\ngit status\ncd ~/projects\necho hello\n")

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_bash_history()
    assert result["status"] == "success"
    assert result["count"] == 4
    assert len(result["entries"]) == 4
    assert "ls -la" in result["entries"]
    assert "git status" in result["entries"]
    assert "cd ~/projects" in result["entries"]
    assert "echo hello" in result["entries"]


def test_read_bash_history_with_limit(tmp_path, monkeypatch):
    """Test reading bash history with limit."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # Write 10 history entries
    commands = [f"command{i}\n" for i in range(10)]
    history_file.write_text("".join(commands))

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_bash_history(limit=5)
    assert result["status"] == "success"
    assert result["count"] == 5
    assert len(result["entries"]) == 5


def test_read_bash_history_removes_duplicates(tmp_path, monkeypatch):
    """Test that read_bash_history removes duplicate commands."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # Write duplicate commands
    history_file.write_text("ls\nls\ngit status\nls\necho test\n")

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_bash_history()
    assert result["status"] == "success"
    # Should have unique commands only (most recent first, so duplicates removed)
    assert result["count"] == 3
    assert "ls" in result["entries"]
    assert "git status" in result["entries"]
    assert "echo test" in result["entries"]
    # Check no duplicates
    assert result["entries"].count("ls") == 1


def test_read_bash_history_limit_validation(tmp_path, monkeypatch):
    """Test that read_bash_history validates limit parameter."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("command1\ncommand2\n")

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    # Test with limit too high (should cap at 1000)
    result = read_bash_history(limit=2000)
    assert result["status"] == "success"
    # Should still work, just capped

    # Test with limit too low (should be at least 1)
    result = read_bash_history(limit=0)
    assert result["status"] == "success"
    # Should still work, just minimum 1


def test_read_bash_history_permission_error(tmp_path, monkeypatch):
    """Test read_bash_history handles permission errors gracefully."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("test\n")
    history_file.chmod(0o000)  # Remove all permissions

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    try:
        result = read_bash_history()
        # Should handle error gracefully
        assert result["status"] == "error"
        assert "Permission" in result["message"] or "permission" in result["message"].lower()
    finally:
        # Restore permissions for cleanup
        history_file.chmod(0o644)


def test_read_conversation_history_nonexistent(tmp_path, monkeypatch):
    """Test reading conversation history when logs don't exist."""
    logs_dir = tmp_path / ".config" / "flourish" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_conversation_history()
    assert result["status"] == "success"
    assert result["count"] == 0
    assert "No session logs" in result["message"]


def test_read_conversation_history_empty_logs_dir(tmp_path, monkeypatch):
    """Test reading conversation history from empty logs directory."""
    logs_dir = tmp_path / ".config" / "flourish" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_conversation_history()
    assert result["status"] == "success"
    assert result["count"] == 0


def test_read_conversation_history_with_entries(tmp_path, monkeypatch):
    """Test reading conversation history with log entries."""
    logs_dir = tmp_path / ".config" / "flourish" / "logs"
    session_dir = logs_dir / "session_2025-01-26_10-00-00"
    session_dir.mkdir(parents=True, exist_ok=True)

    conversation_log = session_dir / "conversation.log"
    # Write log entries in the format: "timestamp - name - level - JSON_MESSAGE"
    log_entries = [
        '2025-01-26 10:00:00 - flourish.conversation - INFO - {"timestamp":"2025-01-26T10:00:00","event":"conversation","role":"user","content":"Hello"}\n',
        '2025-01-26 10:00:01 - flourish.conversation - INFO - {"timestamp":"2025-01-26T10:00:01","event":"conversation","role":"agent","content":"Hi there!"}\n',
        '2025-01-26 10:00:02 - flourish.conversation - INFO - {"timestamp":"2025-01-26T10:00:02","event":"tool_call","tool":"execute_bash","parameters":{"cmd":"ls"},"success":true}\n',
    ]
    conversation_log.write_text("".join(log_entries))

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_conversation_history()
    assert result["status"] == "success"
    assert result["count"] == 3
    assert len(result["entries"]) == 3
    assert result["session_dir"] == str(session_dir)
    # Check that entries have expected structure
    for entry in result["entries"]:
        assert "timestamp" in entry
        assert "event" in entry
        assert "data" in entry


def test_read_conversation_history_with_limit(tmp_path, monkeypatch):
    """Test reading conversation history with limit."""
    logs_dir = tmp_path / ".config" / "flourish" / "logs"
    session_dir = logs_dir / "session_2025-01-26_10-00-00"
    session_dir.mkdir(parents=True, exist_ok=True)

    conversation_log = session_dir / "conversation.log"
    # Write 10 log entries
    log_entries = []
    for i in range(10):
        log_entries.append(
            f'2025-01-26 10:00:{i:02d} - flourish.conversation - INFO - {{"timestamp":"2025-01-26T10:00:{i:02d}","event":"conversation","role":"user","content":"Message {i}"}}\n'
        )
    conversation_log.write_text("".join(log_entries))

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_conversation_history(limit=5)
    assert result["status"] == "success"
    assert result["count"] == 5
    assert len(result["entries"]) == 5


def test_read_conversation_history_finds_most_recent(tmp_path, monkeypatch):
    """Test that read_conversation_history finds the most recent session."""
    logs_dir = tmp_path / ".config" / "flourish" / "logs"
    # Create two session directories
    old_session = logs_dir / "session_2025-01-26_09-00-00"
    old_session.mkdir(parents=True, exist_ok=True)
    old_log = old_session / "conversation.log"
    old_log.write_text(
        '2025-01-26 09:00:00 - flourish.conversation - INFO - {"event":"conversation","role":"user","content":"Old message"}\n'
    )
    # Ensure old session has older mtime
    old_time = time.time() - 100
    old_log.touch()
    os.utime(old_log, (old_time, old_time))
    os.utime(old_session, (old_time, old_time))

    new_session = logs_dir / "session_2025-01-26_10-00-00"
    new_session.mkdir(parents=True, exist_ok=True)
    new_log = new_session / "conversation.log"
    new_log.write_text(
        '2025-01-26 10:00:00 - flourish.conversation - INFO - {"event":"conversation","role":"user","content":"New message"}\n'
    )
    # Ensure new session has newer mtime
    new_time = time.time()
    new_log.touch()
    os.utime(new_log, (new_time, new_time))
    os.utime(new_session, (new_time, new_time))

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    result = read_conversation_history()
    assert result["status"] == "success"
    assert result["session_dir"] == str(new_session)
    assert "New message" in str(result["entries"])


def test_get_current_datetime():
    """Test getting current date and time."""
    result = get_current_datetime()
    assert result["status"] == "success"
    assert "iso_timestamp" in result
    assert "local_datetime" in result
    assert "date" in result
    assert "time" in result
    assert "utc_datetime" in result
    # Verify format
    assert len(result["date"]) == 10  # YYYY-MM-DD
    assert len(result["time"]) == 8  # HH:MM:SS
    assert "UTC" in result["utc_datetime"]
