"""History-related tools for reading command and conversation history."""

import json
import time
from pathlib import Path
from typing import Any

from ...logging import log_tool_call


def read_bash_history(limit: int = 50) -> dict[str, Any]:
    """
    Read bash command history from the Flourish history file.

    This tool allows the agent to see what bash commands have been executed previously,
    which can help understand user workflow and context.

    Args:
        limit: Maximum number of history entries to return (default: 50, max: 1000).

    Returns:
        A dictionary with status, history entries, and count.
    """
    t0 = time.perf_counter()
    history_file = Path.home() / ".config" / "flourish" / "history"

    # Validate limit
    if limit < 1:
        limit = 1
    if limit > 1000:
        limit = 1000

    result: dict[str, Any] = {
        "status": "success",
        "history_file": str(history_file),
        "entries": [],
        "count": 0,
    }

    try:
        if not history_file.exists():
            result["message"] = "History file does not exist yet"
            log_tool_call(
                "read_bash_history", {"limit": limit}, result, success=True,
                duration_seconds=time.perf_counter() - t0,
            )
            return result

        # Read history file (prompt-toolkit FileHistory format: one command per line)
        with open(history_file, encoding="utf-8") as f:
            lines = f.readlines()

        # Filter out empty lines and get unique commands (most recent first)
        commands = []
        seen = set()
        for line in reversed(lines):  # Start from most recent
            cmd = line.strip()
            if cmd and cmd not in seen:
                commands.append(cmd)
                seen.add(cmd)
                if len(commands) >= limit:
                    break

        # Reverse to show oldest first (or keep newest first - let's keep newest first)
        result["entries"] = commands
        result["count"] = len(commands)
        result["message"] = f"Retrieved {len(commands)} history entries"

    except PermissionError:
        result["status"] = "error"
        result["message"] = "Permission denied reading history file"
        log_tool_call(
            "read_bash_history", {"limit": limit}, result, success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Error reading history: {str(e)}"
        log_tool_call(
            "read_bash_history", {"limit": limit}, result, success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result

    log_tool_call(
        "read_bash_history", {"limit": limit}, result, success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result


def read_conversation_history(limit: int = 20) -> dict[str, Any]:
    """
    Read conversation history from the most recent Flourish session log.

    This tool allows the agent to see previous conversations, tool calls, and events
    from the current or most recent session, helping maintain context across interactions.

    Args:
        limit: Maximum number of log entries to return (default: 20, max: 100).

    Returns:
        A dictionary with status, log entries, session info, and count.
    """
    t0 = time.perf_counter()
    logs_dir = Path.home() / ".config" / "flourish" / "logs"

    # Validate limit
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100

    result: dict[str, Any] = {
        "status": "success",
        "session_dir": None,
        "entries": [],
        "count": 0,
    }

    try:
        if not logs_dir.exists():
            result["message"] = "Logs directory does not exist yet"
            log_tool_call(
                "read_conversation_history", {"limit": limit}, result, success=True,
                duration_seconds=time.perf_counter() - t0,
            )
            return result

        # Find most recent session directory
        session_dirs = sorted(
            [d for d in logs_dir.iterdir() if d.is_dir() and d.name.startswith("session_")],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        if not session_dirs:
            result["message"] = "No session logs found"
            log_tool_call(
                "read_conversation_history", {"limit": limit}, result, success=True,
                duration_seconds=time.perf_counter() - t0,
            )
            return result

        # Use most recent session
        latest_session = session_dirs[0]
        conversation_log = latest_session / "conversation.log"

        if not conversation_log.exists():
            result["message"] = "Conversation log file does not exist"
            log_tool_call(
                "read_conversation_history", {"limit": limit}, result, success=True,
                duration_seconds=time.perf_counter() - t0,
            )
            return result

        result["session_dir"] = str(latest_session)

        # Read and parse log entries
        # Format: "timestamp - name - level - JSON_MESSAGE"
        entries = []
        with open(conversation_log, encoding="utf-8") as f:
            lines = f.readlines()

        # Parse entries from most recent first
        for line in reversed(lines[-limit * 2 :]):  # Read more lines to account for formatting
            line = line.strip()
            if not line:
                continue

            # Parse log format: "timestamp - name - level - JSON_MESSAGE"
            # Try to extract JSON part (after the third " - ")
            parts = line.split(" - ", 3)
            if len(parts) >= 4:
                try:
                    log_data = json.loads(parts[3])
                    entries.append(
                        {
                            "timestamp": log_data.get("timestamp", parts[0]),
                            "event": log_data.get("event", "unknown"),
                            "data": log_data,
                        }
                    )
                    if len(entries) >= limit:
                        break
                except json.JSONDecodeError:
                    # Skip malformed entries
                    continue

        # Reverse to show oldest first (chronological order)
        entries.reverse()
        result["entries"] = entries
        result["count"] = len(entries)
        result["message"] = (
            f"Retrieved {len(entries)} conversation log entries from {latest_session.name}"
        )

    except PermissionError:
        result["status"] = "error"
        result["message"] = "Permission denied reading conversation logs"
        log_tool_call(
            "read_conversation_history", {"limit": limit}, result, success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Error reading conversation history: {str(e)}"
        log_tool_call(
            "read_conversation_history", {"limit": limit}, result, success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result

    log_tool_call(
        "read_conversation_history", {"limit": limit}, result, success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result


def _get_latest_conversation_logs(max_sessions: int = 1) -> list[Path]:
    """Return paths to conversation.log from the most recent session(s)."""
    logs_dir = Path.home() / ".config" / "flourish" / "logs"
    if not logs_dir.exists():
        return []

    session_dirs = sorted(
        [d for d in logs_dir.iterdir() if d.is_dir() and d.name.startswith("session_")],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    paths = []
    for session_dir in session_dirs[:max_sessions]:
        log_file = session_dir / "conversation.log"
        if log_file.exists():
            paths.append(log_file)
    return paths


def _parse_tool_calls_from_log(log_path: Path) -> list[dict[str, Any]]:
    """Parse conversation.log and yield tool_call events as dicts."""
    tool_calls = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" - ", 3)
            if len(parts) < 4:
                continue
            try:
                log_data = json.loads(parts[3])
                if log_data.get("event") == "tool_call":
                    tool_calls.append(log_data)
            except json.JSONDecodeError:
                continue
    return tool_calls


def get_tool_call_stats(
    max_sessions: int = 5,
    include_recent: int = 20,
    tool_context: Any = None,
) -> dict[str, Any]:
    """
    Parse tool-call history from Flourish session logs and return aggregated stats.

    Reads conversation.log from the most recent session(s), filters for tool_call events,
    and returns per-tool counts, success rates, and duration statistics. Useful for
    analytics and understanding which tools are used most and how long they take.

    Args:
        max_sessions: Number of most recent session logs to include (default: 5).
        include_recent: Number of most recent tool calls to list in the result (default: 20, 0 to omit).
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status, session sources, total_tool_calls, by_tool stats
        (count, success_count, success_rate, total_duration_seconds, avg_duration_seconds),
        and optionally recent_calls.
    """
    t0 = time.perf_counter()
    result: dict[str, Any] = {
        "status": "success",
        "sessions_parsed": 0,
        "log_files": [],
        "total_tool_calls": 0,
        "by_tool": {},
        "recent_calls": [],
    }

    try:
        log_files = _get_latest_conversation_logs(max_sessions=max_sessions)
        if not log_files:
            result["message"] = "No session conversation logs found"
            log_tool_call(
                "get_tool_call_stats",
                {"max_sessions": max_sessions, "include_recent": include_recent},
                result,
                success=True,
                duration_seconds=time.perf_counter() - t0,
            )
            return result

        result["log_files"] = [str(p) for p in log_files]
        result["sessions_parsed"] = len(log_files)

        # Collect all tool calls (oldest first across sessions)
        all_calls: list[dict[str, Any]] = []
        for log_path in reversed(log_files):
            all_calls.extend(_parse_tool_calls_from_log(log_path))

        result["total_tool_calls"] = len(all_calls)

        # Aggregate by tool name
        by_tool: dict[str, dict[str, Any]] = {}
        for entry in all_calls:
            tool = entry.get("tool", "unknown")
            if tool not in by_tool:
                by_tool[tool] = {
                    "count": 0,
                    "success_count": 0,
                    "total_duration_seconds": 0.0,
                    "durations": [],
                }
            by_tool[tool]["count"] += 1
            if entry.get("success", False):
                by_tool[tool]["success_count"] += 1
            dur = entry.get("duration_seconds")
            if dur is not None:
                by_tool[tool]["total_duration_seconds"] += float(dur)
                by_tool[tool]["durations"].append(float(dur))

        # Add derived stats per tool
        for tool, stats in by_tool.items():
            count = stats["count"]
            stats["success_rate"] = (
                round(stats["success_count"] / count, 4) if count else 0.0
            )
            stats["avg_duration_seconds"] = (
                round(stats["total_duration_seconds"] / len(stats["durations"]), 4)
                if stats["durations"]
                else None
            )
            del stats["durations"]

        result["by_tool"] = by_tool

        # Optionally include last N calls (tool, timestamp, success, duration_seconds)
        if include_recent > 0 and all_calls:
            recent = all_calls[-include_recent:]
            result["recent_calls"] = [
                {
                    "tool": e.get("tool", "unknown"),
                    "timestamp": e.get("timestamp"),
                    "success": e.get("success", False),
                    "duration_seconds": e.get("duration_seconds"),
                }
                for e in recent
            ]

        result["message"] = (
            f"Parsed {len(all_calls)} tool calls from {len(log_files)} session(s)"
        )

    except PermissionError:
        result["status"] = "error"
        result["message"] = "Permission denied reading conversation logs"
        log_tool_call(
            "get_tool_call_stats",
            {"max_sessions": max_sessions, "include_recent": include_recent},
            result,
            success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Error parsing tool call history: {str(e)}"
        log_tool_call(
            "get_tool_call_stats",
            {"max_sessions": max_sessions, "include_recent": include_recent},
            result,
            success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result

    log_tool_call(
        "get_tool_call_stats",
        {"max_sessions": max_sessions, "include_recent": include_recent},
        result,
        success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result
