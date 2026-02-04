"""Unit tests for history tools: get_tool_call_stats and log parsing."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from flouri.tools.history import history_tools


@pytest.fixture
def temp_conversation_log(tmp_path):
    """Create a temporary conversation.log with tool_call events."""
    session_dir = tmp_path / "session_2026-01-01_12-00-00"
    session_dir.mkdir()
    log_file = session_dir / "conversation.log"
    # Log format: "timestamp - name - level - JSON_MESSAGE"
    lines = [
        "2026-01-01 12:00:01 - flouri.conversation - INFO - "
        + json.dumps(
            {
                "timestamp": "2026-01-01T12:00:01",
                "event": "tool_call",
                "tool": "execute_bash",
                "parameters": {"cmd": "ls"},
                "success": True,
                "duration_seconds": 0.05,
            }
        ),
        "2026-01-01 12:00:02 - flouri.conversation - INFO - "
        + json.dumps(
            {
                "timestamp": "2026-01-01T12:00:02",
                "event": "tool_call",
                "tool": "execute_bash",
                "parameters": {"cmd": "pwd"},
                "success": True,
                "duration_seconds": 0.02,
            }
        ),
        "2026-01-01 12:00:03 - flouri.conversation - INFO - "
        + json.dumps(
            {
                "timestamp": "2026-01-01T12:00:03",
                "event": "tool_call",
                "tool": "ros2_topic_list",
                "parameters": {},
                "success": False,
                "duration_seconds": 1.5,
            }
        ),
    ]
    log_file.write_text("\n".join(lines), encoding="utf-8")
    return log_file


def test_parse_tool_calls_from_log(temp_conversation_log):
    """_parse_tool_calls_from_log returns tool_call events."""
    calls = history_tools._parse_tool_calls_from_log(temp_conversation_log)
    assert len(calls) == 3
    assert calls[0]["tool"] == "execute_bash"
    assert calls[0]["duration_seconds"] == 0.05
    assert calls[2]["tool"] == "ros2_topic_list"
    assert calls[2]["success"] is False


def test_get_tool_call_stats_with_mock_logs(temp_conversation_log):
    """get_tool_call_stats returns aggregated stats when logs exist."""
    with patch.object(history_tools, "_get_latest_conversation_logs") as mock_get:
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            mock_get.return_value = [temp_conversation_log]
            result = history_tools.get_tool_call_stats(max_sessions=1, include_recent=5)

    assert result["status"] == "success"
    assert result["total_tool_calls"] == 3
    assert result["sessions_parsed"] == 1
    assert "execute_bash" in result["by_tool"]
    assert result["by_tool"]["execute_bash"]["count"] == 2
    assert result["by_tool"]["execute_bash"]["success_count"] == 2
    assert result["by_tool"]["execute_bash"]["success_rate"] == 1.0
    assert result["by_tool"]["execute_bash"]["avg_duration_seconds"] == pytest.approx(0.035)
    assert result["by_tool"]["ros2_topic_list"]["count"] == 1
    assert result["by_tool"]["ros2_topic_list"]["success_count"] == 0
    assert len(result["recent_calls"]) == 3


def test_get_tool_call_stats_no_logs():
    """get_tool_call_stats returns empty stats when no session logs exist."""
    with patch.object(history_tools, "_get_latest_conversation_logs", return_value=[]):
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            result = history_tools.get_tool_call_stats(max_sessions=5, include_recent=0)

    assert result["status"] == "success"
    assert result["total_tool_calls"] == 0
    assert result["by_tool"] == {}
    assert result["recent_calls"] == []
    assert "message" in result


def test_get_tool_call_stats_include_recent_zero():
    """include_recent=0 omits recent_calls."""
    with patch.object(history_tools, "_get_latest_conversation_logs", return_value=[]):
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            result = history_tools.get_tool_call_stats(include_recent=0)
    assert "recent_calls" in result
    assert result["recent_calls"] == []


def test_get_tool_call_stats_permission_error():
    """get_tool_call_stats returns error on PermissionError."""
    with patch.object(
        history_tools, "_get_latest_conversation_logs", side_effect=PermissionError("denied")
    ):
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            result = history_tools.get_tool_call_stats(max_sessions=1)
    assert result["status"] == "error"
    assert "Permission" in result["message"]


def test_get_tool_call_stats_generic_exception():
    """get_tool_call_stats returns error on generic Exception."""
    with patch.object(
        history_tools, "_get_latest_conversation_logs", side_effect=RuntimeError("parse failed")
    ):
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            result = history_tools.get_tool_call_stats(max_sessions=1)
    assert result["status"] == "error"
    assert "Error" in result["message"]


def test_read_bash_history_exception():
    """read_bash_history returns error when reading raises."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", side_effect=OSError(13, "Permission denied")):
            with patch("flouri.tools.history.history_tools.log_tool_call"):
                result = history_tools.read_bash_history(limit=10)
    assert result["status"] == "error"
    assert "message" in result


def test_read_bash_history_success_with_entries(tmp_path):
    """read_bash_history returns entries when history file exists with content."""
    config_dir = tmp_path / ".config" / "flouri"
    config_dir.mkdir(parents=True)
    history_file = config_dir / "history"
    history_file.write_text("ls -la\npwd\ncd /tmp\n", encoding="utf-8")
    with patch.object(Path, "home", return_value=tmp_path):
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            result = history_tools.read_bash_history(limit=50)
    assert result["status"] == "success"
    assert result["count"] == 3
    assert len(result["entries"]) == 3
    assert "ls -la" in result["entries"] or "cd /tmp" in result["entries"]


def test_read_conversation_history_no_logs_dir():
    """read_conversation_history returns success with message when logs dir does not exist."""
    with patch.object(Path, "home") as mock_home:
        mock_home.return_value = Path("/nonexistent")
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            result = history_tools.read_conversation_history(limit=5)
    assert result["status"] == "success"
    assert result["entries"] == []
    assert "does not exist" in result.get("message", "")


def test_read_conversation_history_no_sessions(tmp_path):
    """read_conversation_history returns success with message when no session dirs."""
    logs_dir = tmp_path / ".config" / "flouri" / "logs"
    logs_dir.mkdir(parents=True)
    with patch.object(Path, "home", return_value=tmp_path):
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            result = history_tools.read_conversation_history(limit=5)
    assert result["status"] == "success"
    assert result["entries"] == []
    assert "No session" in result.get("message", "")


def test_read_conversation_history_no_log_file(tmp_path):
    """read_conversation_history returns success when session dir exists but conversation.log does not."""
    session_dir = tmp_path / ".config" / "flouri" / "logs" / "session_2026-01-01_12-00-00"
    session_dir.mkdir(parents=True)
    # No conversation.log
    with patch.object(Path, "home", return_value=tmp_path):
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            result = history_tools.read_conversation_history(limit=5)
    assert result["status"] == "success"
    assert result["entries"] == []
    assert "does not exist" in result.get("message", "")


def test_read_conversation_history_permission_error(tmp_path):
    """read_conversation_history returns error on PermissionError."""
    session_dir = tmp_path / ".config" / "flouri" / "logs" / "session_2026-01-01_12-00-00"
    session_dir.mkdir(parents=True)
    log_file = session_dir / "conversation.log"
    log_file.write_text("")
    with patch.object(Path, "home", return_value=tmp_path):
        with patch("builtins.open", side_effect=PermissionError("denied")):
            with patch("flouri.tools.history.history_tools.log_tool_call"):
                result = history_tools.read_conversation_history(limit=5)
    assert result["status"] == "error"
    assert "Permission" in result["message"]


def test_read_conversation_history_success_with_entries(tmp_path):
    """read_conversation_history returns entries when conversation.log exists with valid lines."""
    session_dir = tmp_path / ".config" / "flouri" / "logs" / "session_2026-01-01_12-00-00"
    session_dir.mkdir(parents=True)
    log_file = session_dir / "conversation.log"
    lines = [
        "2026-01-01 12:00:01 - flouri.conversation - INFO - "
        + json.dumps(
            {
                "timestamp": "2026-01-01T12:00:01",
                "event": "conversation",
                "role": "user",
                "content": "hi",
            }
        ),
        "2026-01-01 12:00:02 - flouri.conversation - INFO - "
        + json.dumps(
            {"timestamp": "2026-01-01T12:00:02", "event": "tool_call", "tool": "execute_bash"}
        ),
    ]
    log_file.write_text("\n".join(lines), encoding="utf-8")

    with patch.object(Path, "home", return_value=tmp_path):
        with patch("flouri.tools.history.history_tools.log_tool_call"):
            result = history_tools.read_conversation_history(limit=10)

    assert result["status"] == "success"
    assert result["count"] == 2
    assert len(result["entries"]) == 2
    assert result["entries"][0]["event"] in ("conversation", "tool_call")
    assert "session_dir" in result
