"""Unit tests for logging module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from flourish.logging import logger as log_module


def test_initialize_session_log_creates_session_dir(tmp_path):
    """initialize_session_log creates timestamped session dir and log files."""
    with patch.object(log_module, "BASE_LOGS_DIR", tmp_path):
        with patch.dict(log_module.__dict__, {"_conversation_logger": None, "_terminal_logger": None}):
            session_dir = log_module.initialize_session_log()
            assert session_dir is not None
            assert session_dir.is_dir()
            assert (session_dir / "conversation.log").exists()
            assert (session_dir / "terminal.log").exists()
            assert log_module.get_session_dir() == session_dir


def test_get_session_dir_before_init_returns_none():
    """get_session_dir returns None when session not initialized."""
    with patch.dict(log_module.__dict__, {"_session_dir": None}):
        assert log_module.get_session_dir() is None


def test_setup_conversation_logger_creates_session_dir_when_none(tmp_path):
    """_setup_conversation_logger creates _session_dir when both it and _conversation_log_file are None."""
    with patch.object(log_module, "BASE_LOGS_DIR", tmp_path):
        with patch.dict(
            log_module.__dict__,
            {"_conversation_logger": None, "_conversation_log_file": None, "_session_dir": None},
        ):
            logger = log_module._setup_conversation_logger()
            assert logger is not None
            assert log_module._session_dir is not None
            assert log_module._conversation_log_file == log_module._session_dir / "conversation.log"
    # Session dir was created under tmp_path
    session_dirs = list(tmp_path.glob("session_*"))
    assert len(session_dirs) == 1
    assert (session_dirs[0] / "conversation.log").exists()


def test_setup_terminal_logger_creates_session_dir_when_none(tmp_path):
    """_setup_terminal_logger creates _session_dir when both it and _terminal_log_file are None."""
    with patch.object(log_module, "BASE_LOGS_DIR", tmp_path):
        with patch.dict(
            log_module.__dict__,
            {"_terminal_logger": None, "_terminal_log_file": None, "_session_dir": None},
        ):
            logger = log_module._setup_terminal_logger()
            assert logger is not None
            assert log_module._session_dir is not None
            assert log_module._terminal_log_file == log_module._session_dir / "terminal.log"
    session_dirs = list(tmp_path.glob("session_*"))
    assert len(session_dirs) >= 1
    assert (session_dirs[0] / "terminal.log").exists()


def test_log_session_end():
    """log_session_end writes session_end event to conversation log."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_conversation_logger", return_value=mock_logger):
        log_module.log_session_end()
    mock_logger.info.assert_called_once()
    data = json.loads(mock_logger.info.call_args[0][0])
    assert data["event"] == "session_end"


def test_log_tool_call_json_fallback():
    """log_tool_call falls back to warning + info when JSON serialization fails."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_conversation_logger", return_value=mock_logger):
        # Cause json.dumps to fail by passing a result that custom serializer could break on
        with patch("flourish.logging.logger.json.dumps", side_effect=TypeError("not serializable")):
            log_module.log_tool_call("t", {}, "result", success=True)
    mock_logger.warning.assert_called_once()
    assert "Failed to log tool call" in mock_logger.warning.call_args[0][0]
    mock_logger.info.assert_called_once()
    assert "Tool: t" in mock_logger.info.call_args[0][0]


def test_log_conversation_success():
    """log_conversation writes JSON conversation event."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_conversation_logger", return_value=mock_logger):
        log_module.log_conversation("user", "hello", metadata={"key": "value"})
    mock_logger.info.assert_called_once()
    data = json.loads(mock_logger.info.call_args[0][0])
    assert data["event"] == "conversation"
    assert data["role"] == "user"
    assert data["content"] == "hello"
    assert data["metadata"] == {"key": "value"}


def test_log_conversation_truncates_long_content():
    """log_conversation truncates content over 2000 chars."""
    mock_logger = MagicMock()
    long_content = "x" * 2500
    with patch.object(log_module, "_setup_conversation_logger", return_value=mock_logger):
        log_module.log_conversation("agent", long_content)
    data = json.loads(mock_logger.info.call_args[0][0])
    assert len(data["content"]) == 2000 + len("... [truncated]")
    assert data["content"].endswith("... [truncated]")


def test_log_conversation_json_fallback():
    """log_conversation falls back when JSON serialization fails."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_conversation_logger", return_value=mock_logger):
        with patch("flourish.logging.logger.json.dumps", side_effect=ValueError("bad")):
            log_module.log_conversation("user", "hi")
    mock_logger.warning.assert_called_once()
    mock_logger.info.assert_called_once()


def test_log_terminal_output_success():
    """log_terminal_output writes JSON terminal log entry."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_terminal_logger", return_value=mock_logger):
        log_module.log_terminal_output("ls -la", stdout="out", stderr="err", exit_code=0, cwd="/tmp")
    mock_logger.info.assert_called_once()
    data = json.loads(mock_logger.info.call_args[0][0])
    assert data["command"] == "ls -la"
    assert data["stdout"] == "out"
    assert data["stderr"] == "err"
    assert data["cwd"] == "/tmp"


def test_log_terminal_output_json_fallback():
    """log_terminal_output falls back when JSON fails and logs stdout/stderr."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_terminal_logger", return_value=mock_logger):
        with patch("flourish.logging.logger.json.dumps", side_effect=TypeError("err")):
            log_module.log_terminal_output("cmd", stdout="out", stderr="err")
    mock_logger.warning.assert_called_once()
    assert mock_logger.info.call_count >= 2  # Command line + STDOUT/STDERR


def test_log_terminal_error_success():
    """log_terminal_error writes JSON error entry."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_terminal_logger", return_value=mock_logger):
        log_module.log_terminal_error("bad_cmd", "permission denied", cwd="/home")
    mock_logger.error.assert_called_once()
    data = json.loads(mock_logger.error.call_args[0][0])
    assert data["event"] == "error"
    assert data["command"] == "bad_cmd"
    assert data["error"] == "permission denied"


def test_log_terminal_error_json_fallback():
    """log_terminal_error falls back when JSON fails."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_terminal_logger", return_value=mock_logger):
        with patch("flourish.logging.logger.json.dumps", side_effect=RuntimeError("err")):
            log_module.log_terminal_error("cmd", "err")
    mock_logger.warning.assert_called_once()
    mock_logger.error.assert_called_once()


def test_log_tool_call_includes_duration_seconds():
    """log_tool_call adds duration_seconds to log entry when provided."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_conversation_logger", return_value=mock_logger):
        log_module.log_tool_call(
            "test_tool",
            {"arg": "value"},
            {"result": "ok"},
            success=True,
            duration_seconds=1.2345,
        )

    mock_logger.info.assert_called_once()
    call_arg = mock_logger.info.call_args[0][0]
    data = json.loads(call_arg)
    assert data["event"] == "tool_call"
    assert data["tool"] == "test_tool"
    assert data["parameters"] == {"arg": "value"}
    assert data["success"] is True
    assert data["duration_seconds"] == 1.2345


def test_log_tool_call_without_duration():
    """log_tool_call omits duration_seconds when not provided."""
    mock_logger = MagicMock()
    with patch.object(log_module, "_setup_conversation_logger", return_value=mock_logger):
        log_module.log_tool_call("other_tool", {}, "result", success=False)

    call_arg = mock_logger.info.call_args[0][0]
    data = json.loads(call_arg)
    assert "duration_seconds" not in data
    assert data["success"] is False


def test_log_tool_call_truncates_long_result():
    """log_tool_call truncates result string over 1000 chars."""
    mock_logger = MagicMock()
    long_result = "x" * 1500
    with patch.object(log_module, "_setup_conversation_logger", return_value=mock_logger):
        log_module.log_tool_call("tool", {}, long_result, success=True)

    call_arg = mock_logger.info.call_args[0][0]
    data = json.loads(call_arg)
    assert len(data["result"]) == 1000 + len("... [truncated]")
    assert data["result"].endswith("... [truncated]")
