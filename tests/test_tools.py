"""Tests for tools module."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from flourish.tools.tools import (
    add_to_allowlist,
    add_to_blacklist,
    execute_bash,
    get_bash_tools,
    get_user,
    is_in_allowlist,
    is_in_blacklist,
    list_allowlist,
    list_blacklist,
    read_history,
    remove_from_allowlist,
    remove_from_blacklist,
    set_allowlist_blacklist,
    set_cwd,
)


@pytest.fixture
def reset_globals():
    """Reset global variables before each test."""
    from flourish.tools.tools import (
        GLOBAL_ALLOWLIST,
        GLOBAL_BLACKLIST,
        GLOBAL_CWD,
    )

    GLOBAL_ALLOWLIST = None
    GLOBAL_BLACKLIST = None
    GLOBAL_CWD = str(Path.cwd())
    yield
    GLOBAL_ALLOWLIST = None
    GLOBAL_BLACKLIST = None
    GLOBAL_CWD = str(Path.cwd())


def test_set_cwd(tmp_path, reset_globals):
    """Test setting current working directory."""
    result = set_cwd(str(tmp_path))
    assert "Working directory set to" in result
    from flourish.tools.tools import GLOBAL_CWD

    assert GLOBAL_CWD == str(tmp_path)


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
    from flourish.tools.tools import GLOBAL_ALLOWLIST, GLOBAL_BLACKLIST

    assert "ls" in GLOBAL_ALLOWLIST
    assert "rm" in GLOBAL_BLACKLIST


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


def test_execute_bash_not_in_allowlist(reset_globals):
    """Test that commands not in allowlist are still executed (auto-added)."""
    set_allowlist_blacklist(allowlist=["ls"], blacklist=None)
    result = execute_bash("echo test", tool_context=None)
    # Command should be auto-added to allowlist and executed
    assert result["status"] == "success"


def test_add_to_allowlist(reset_globals):
    """Test adding command to allowlist."""
    set_allowlist_blacklist(allowlist=[], blacklist=None)
    result = add_to_allowlist("ls", tool_context=None)
    assert result["status"] == "success"
    from flourish.tools.tools import GLOBAL_ALLOWLIST

    assert "ls" in GLOBAL_ALLOWLIST


def test_add_to_blacklist(reset_globals):
    """Test adding command to blacklist."""
    set_allowlist_blacklist(allowlist=None, blacklist=[])
    result = add_to_blacklist("rm", tool_context=None)
    assert result["status"] == "success"
    from flourish.tools.tools import GLOBAL_BLACKLIST

    assert "rm" in GLOBAL_BLACKLIST


def test_remove_from_allowlist(reset_globals):
    """Test removing command from allowlist."""
    set_allowlist_blacklist(allowlist=["ls"], blacklist=None)
    result = remove_from_allowlist("ls", tool_context=None)
    assert result["status"] == "success"
    from flourish.tools.tools import GLOBAL_ALLOWLIST

    assert "ls" not in GLOBAL_ALLOWLIST


def test_remove_from_blacklist(reset_globals):
    """Test removing command from blacklist."""
    set_allowlist_blacklist(allowlist=None, blacklist=["rm"])
    result = remove_from_blacklist("rm", tool_context=None)
    assert result["status"] == "success"
    from flourish.tools.tools import GLOBAL_BLACKLIST

    assert "rm" not in GLOBAL_BLACKLIST


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


def test_read_history_nonexistent(tmp_path, monkeypatch):
    """Test reading history when file doesn't exist."""
    # Create the config directory structure but no history file
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    
    result = read_history()
    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["entries"] == []
    assert "does not exist" in result["message"]


def test_read_history_empty_file(tmp_path, monkeypatch):
    """Test reading history from empty file."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.touch()
    
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    
    result = read_history()
    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["entries"] == []


def test_read_history_with_commands(tmp_path, monkeypatch):
    """Test reading history with commands."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write some history entries (one per line, as prompt-toolkit format)
    history_file.write_text("ls -la\ngit status\ncd ~/projects\necho hello\n")
    
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    
    result = read_history()
    assert result["status"] == "success"
    assert result["count"] == 4
    assert len(result["entries"]) == 4
    assert "ls -la" in result["entries"]
    assert "git status" in result["entries"]
    assert "cd ~/projects" in result["entries"]
    assert "echo hello" in result["entries"]


def test_read_history_with_limit(tmp_path, monkeypatch):
    """Test reading history with limit."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write 10 history entries
    commands = [f"command{i}\n" for i in range(10)]
    history_file.write_text("".join(commands))
    
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    
    result = read_history(limit=5)
    assert result["status"] == "success"
    assert result["count"] == 5
    assert len(result["entries"]) == 5


def test_read_history_removes_duplicates(tmp_path, monkeypatch):
    """Test that read_history removes duplicate commands."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write duplicate commands
    history_file.write_text("ls\nls\ngit status\nls\necho test\n")
    
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    
    result = read_history()
    assert result["status"] == "success"
    # Should have unique commands only (most recent first, so duplicates removed)
    assert result["count"] == 3
    assert "ls" in result["entries"]
    assert "git status" in result["entries"]
    assert "echo test" in result["entries"]
    # Check no duplicates
    assert result["entries"].count("ls") == 1


def test_read_history_limit_validation(tmp_path, monkeypatch):
    """Test that read_history validates limit parameter."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("command1\ncommand2\n")
    
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    
    # Test with limit too high (should cap at 1000)
    result = read_history(limit=2000)
    assert result["status"] == "success"
    # Should still work, just capped
    
    # Test with limit too low (should be at least 1)
    result = read_history(limit=0)
    assert result["status"] == "success"
    # Should still work, just minimum 1


def test_read_history_permission_error(tmp_path, monkeypatch):
    """Test read_history handles permission errors gracefully."""
    history_file = tmp_path / ".config" / "flourish" / "history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.write_text("test\n")
    history_file.chmod(0o000)  # Remove all permissions
    
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    
    try:
        result = read_history()
        # Should handle error gracefully
        assert result["status"] == "error"
        assert "Permission" in result["message"] or "permission" in result["message"].lower()
    finally:
        # Restore permissions for cleanup
        history_file.chmod(0o644)
