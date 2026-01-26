"""Logging utilities for Flourish."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure base logs directory
BASE_LOGS_DIR = Path.home() / ".config" / "flourish" / "logs"
BASE_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instances and log files
_conversation_logger: logging.Logger | None = None
_terminal_logger: logging.Logger | None = None
_session_dir: Path | None = None
_conversation_log_file: Path | None = None
_terminal_log_file: Path | None = None


def initialize_session_log() -> Path:
    """Initialize the session log directory and files at the beginning of a session.

    Creates a timestamped folder with two log files:
    - conversation.log: For agent conversations and tool calls
    - terminal.log: For terminal output and errors

    Returns:
        Path to the created session directory.
    """
    global _conversation_logger, _terminal_logger, _session_dir
    global _conversation_log_file, _terminal_log_file

    # Create timestamped session directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    _session_dir = BASE_LOGS_DIR / f"session_{timestamp}"
    _session_dir.mkdir(parents=True, exist_ok=True)

    # Create log files
    _conversation_log_file = _session_dir / "conversation.log"
    _terminal_log_file = _session_dir / "terminal.log"

    # Reset loggers to create new handlers
    _conversation_logger = None
    _terminal_logger = None

    # Set up both loggers
    conversation_logger = _setup_conversation_logger()
    terminal_logger = _setup_terminal_logger()

    # Log session start in conversation log
    session_start = {
        "timestamp": datetime.now().isoformat(),
        "event": "session_start",
            "message": "Flourish session started",
    }

    conversation_logger.info(json.dumps(session_start))

    return _session_dir


def _setup_conversation_logger() -> logging.Logger:
    """Set up the logger for conversations and tool calls.

    Returns:
        Configured logger instance for conversations.
    """
    global _conversation_logger, _conversation_log_file

    # Return existing logger if already set up
    if _conversation_logger is not None and _conversation_logger.handlers:
        return _conversation_logger

    # Create logger
    logger = logging.getLogger("flourish.conversation")
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Use existing log file or create new one
    if _conversation_log_file is None:
        if _session_dir is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            _session_dir = BASE_LOGS_DIR / f"session_{timestamp}"
            _session_dir.mkdir(parents=True, exist_ok=True)
        _conversation_log_file = _session_dir / "conversation.log"

    # Create file handler
    file_handler = logging.FileHandler(_conversation_log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    _conversation_logger = logger

    return logger


def _setup_terminal_logger() -> logging.Logger:
    """Set up the logger for terminal output and errors.

    Returns:
        Configured logger instance for terminal output.
    """
    global _terminal_logger, _terminal_log_file

    # Return existing logger if already set up
    if _terminal_logger is not None and _terminal_logger.handlers:
        return _terminal_logger

    # Create logger
    logger = logging.getLogger("flourish.terminal")
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Use existing log file or create new one
    if _terminal_log_file is None:
        if _session_dir is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            _session_dir = BASE_LOGS_DIR / f"session_{timestamp}"
            _session_dir.mkdir(parents=True, exist_ok=True)
        _terminal_log_file = _session_dir / "terminal.log"

    # Create file handler
    file_handler = logging.FileHandler(_terminal_log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Create formatter for terminal output (simpler format)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    _terminal_logger = logger

    return logger


def log_tool_call(
    tool_name: str,
    parameters: dict[str, Any],
    result: Any,
    success: bool = True,
) -> None:
    """Log a tool call to the conversation log file.

    Args:
        tool_name: Name of the tool that was called
        parameters: Dictionary of parameters passed to the tool
        result: Result returned by the tool (will be converted to string)
        success: Whether the tool call was successful
    """
    logger = _setup_conversation_logger()

    # Convert result to string, truncating if too long
    result_str = str(result)
    if len(result_str) > 1000:
        result_str = result_str[:1000] + "... [truncated]"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "tool_call",
        "tool": tool_name,
        "parameters": parameters,
        "result": result_str,
        "success": success,
    }

    # Log as JSON for easy parsing
    try:
        logger.info(json.dumps(log_entry))
    except Exception as e:
        # Fallback to basic logging if JSON serialization fails
        logger.warning(f"Failed to log tool call as JSON: {e}")
        logger.info(f"Tool: {tool_name}, Success: {success}, Params: {parameters}")


def log_conversation(
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Log a conversation message (user or agent) to the conversation log file.

    Args:
        role: Role of the speaker ('user' or 'agent')
        content: The message content
        metadata: Optional additional metadata to include
    """
    logger = _setup_conversation_logger()

    # Truncate long messages
    content_str = content
    if len(content_str) > 2000:
        content_str = content_str[:2000] + "... [truncated]"

    log_entry: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "event": "conversation",
        "role": role,
        "content": content_str,
    }

    if metadata:
        log_entry["metadata"] = metadata

    # Log as JSON for easy parsing
    try:
        logger.info(json.dumps(log_entry))
    except Exception as e:
        # Fallback to basic logging if JSON serialization fails
        logger.warning(f"Failed to log conversation as JSON: {e}")
        logger.info(f"Conversation - {role}: {content_str[:100]}")


def log_terminal_output(
    command: str,
    stdout: str = "",
    stderr: str = "",
    exit_code: int = 0,
    cwd: str | None = None,
) -> None:
    """Log terminal command output and errors to the terminal log file.

    Args:
        command: The command that was executed
        stdout: Standard output from the command
        stderr: Standard error from the command
        exit_code: Exit code of the command
        cwd: Current working directory where command was executed
    """
    logger = _setup_terminal_logger()

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "cwd": cwd or "unknown",
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
    }

    # Log as JSON for easy parsing
    try:
        logger.info(json.dumps(log_entry))
    except Exception as e:
        # Fallback to basic logging if JSON serialization fails
        logger.warning(f"Failed to log terminal output as JSON: {e}")
        logger.info(f"Command: {command}, Exit: {exit_code}")
        if stdout:
            logger.info(f"STDOUT: {stdout}")
        if stderr:
            logger.error(f"STDERR: {stderr}")


def log_terminal_error(
    command: str,
    error: str,
    cwd: str | None = None,
) -> None:
    """Log terminal execution errors to the terminal log file.

    Args:
        command: The command that failed
        error: Error message
        cwd: Current working directory where command was executed
    """
    logger = _setup_terminal_logger()

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "error",
        "command": command,
        "cwd": cwd or "unknown",
        "error": error,
    }

    # Log as JSON for easy parsing
    try:
        logger.error(json.dumps(log_entry))
    except Exception as e:
        # Fallback to basic logging if JSON serialization fails
        logger.warning(f"Failed to log terminal error as JSON: {e}")
        logger.error(f"Command: {command}, Error: {error}")


def log_session_end() -> None:
    """Log session end to the conversation log."""
    logger = _setup_conversation_logger()

    session_end = {
        "timestamp": datetime.now().isoformat(),
        "event": "session_end",
            "message": "Flourish session ended",
    }

    logger.info(json.dumps(session_end))


def get_session_dir() -> Path | None:
    """Get the current session directory.

    Returns:
        Path to the current session directory, or None if not initialized.
    """
    return _session_dir
