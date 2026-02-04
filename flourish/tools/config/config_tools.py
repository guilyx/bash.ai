"""Configuration and allowlist/blacklist management tools."""

import time

from google.adk.tools import ToolContext

from ...logging import log_tool_call
from .. import globals as globals_module


def set_allowlist_blacklist(allowlist: list[str] | None = None, blacklist: list[str] | None = None):
    """Set the global allowlist and blacklist for command validation.

    Args:
        allowlist: List of allowed commands
        blacklist: List of blacklisted commands
    """
    globals_module.GLOBAL_ALLOWLIST = allowlist
    globals_module.GLOBAL_BLACKLIST = blacklist


def add_to_allowlist(command: str, tool_context: ToolContext | None = None) -> dict:
    """
    Add a command to the allowlist.

    Args:
        command: The base command to add (e.g., "ls", "git", "docker", "npm"). Extract from full command if needed.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status, message, and updated allowlist.
    """
    t0 = time.perf_counter()
    # Add to allowlist
    if globals_module.GLOBAL_ALLOWLIST is None:
        globals_module.GLOBAL_ALLOWLIST = []
    if command not in globals_module.GLOBAL_ALLOWLIST:
        globals_module.GLOBAL_ALLOWLIST.append(command)
        # Update config manager if available
        try:
            from ...config.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.add_to_allowlist(command)
        except Exception:
            pass  # Config manager might not be available

    result = {
        "status": "success",
        "message": f"Added '{command}' to allowlist",
        "allowlist": globals_module.GLOBAL_ALLOWLIST.copy(),
    }
    log_tool_call(
        "add_to_allowlist",
        {"command": command},
        result,
        success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result


def remove_from_allowlist(command: str, tool_context: ToolContext | None = None) -> dict:
    """
    Remove a command from the allowlist.

    Args:
        command: The command to remove from the allowlist.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and message.
    """
    t0 = time.perf_counter()
    # Remove from allowlist
    if globals_module.GLOBAL_ALLOWLIST and command in globals_module.GLOBAL_ALLOWLIST:
        globals_module.GLOBAL_ALLOWLIST.remove(command)
        # Update config manager if available
        try:
            from ...config.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.remove_from_allowlist(command)
        except Exception:
            pass

    result = {
        "status": "success",
        "message": f"Removed '{command}' from allowlist",
        "allowlist": (
            globals_module.GLOBAL_ALLOWLIST.copy() if globals_module.GLOBAL_ALLOWLIST else []
        ),
    }
    log_tool_call(
        "remove_from_allowlist",
        {"command": command},
        result,
        success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result


def add_to_blacklist(command: str, tool_context: ToolContext | None = None) -> dict:
    """
    Add a command to the blacklist to permanently block it from execution.

    **USE THIS TOOL AUTOMATICALLY** when you encounter dangerous commands that should never run.
    Don't wait for user permission - proactively block dangerous commands.

    When to use (automatic, don't ask):
    - When you encounter a dangerous or destructive command (e.g., "rm -rf /", "dd if=/dev/zero")
    - When a command could compromise system security
    - When the user requests blocking a specific command
    - When you detect potentially harmful patterns in commands

    After adding, the command will be permanently blocked. Use this for commands
    like "rm -rf /", "dd", "format", "mkfs", "chmod 777 /", etc. that could cause data loss.

    Args:
        command: The base command to blacklist (e.g., "rm", "dd", "format"). Extract the base command from full commands.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status, message, and updated blacklist.
    """
    t0 = time.perf_counter()
    # Add to blacklist
    if globals_module.GLOBAL_BLACKLIST is None:
        globals_module.GLOBAL_BLACKLIST = []
    if command not in globals_module.GLOBAL_BLACKLIST:
        globals_module.GLOBAL_BLACKLIST.append(command)
        # Update config manager if available
        try:
            from ...config.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.add_to_blacklist(command)
        except Exception:
            pass

    result = {
        "status": "success",
        "message": f"Added '{command}' to blacklist",
        "blacklist": globals_module.GLOBAL_BLACKLIST.copy(),
    }
    log_tool_call(
        "add_to_blacklist",
        {"command": command},
        result,
        success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result


def remove_from_blacklist(command: str, tool_context: ToolContext | None = None) -> dict:
    """
    Remove a command from the blacklist.

    Args:
        command: The command to remove from the blacklist.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and message.
    """
    t0 = time.perf_counter()
    # Remove from blacklist
    if globals_module.GLOBAL_BLACKLIST and command in globals_module.GLOBAL_BLACKLIST:
        globals_module.GLOBAL_BLACKLIST.remove(command)
        # Update config manager if available
        try:
            from ...config.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.remove_from_blacklist(command)
        except Exception:
            pass

    result = {
        "status": "success",
        "message": f"Removed '{command}' from blacklist",
        "blacklist": (
            globals_module.GLOBAL_BLACKLIST.copy() if globals_module.GLOBAL_BLACKLIST else []
        ),
    }
    log_tool_call(
        "remove_from_blacklist",
        {"command": command},
        result,
        success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result


def list_allowlist() -> dict:
    """
    List all commands in the allowlist.

    Returns:
        A dictionary with status and the current allowlist.
    """
    t0 = time.perf_counter()
    result = {
        "status": "success",
        "allowlist": (
            globals_module.GLOBAL_ALLOWLIST.copy() if globals_module.GLOBAL_ALLOWLIST else []
        ),
        "count": len(globals_module.GLOBAL_ALLOWLIST) if globals_module.GLOBAL_ALLOWLIST else 0,
    }
    log_tool_call(
        "list_allowlist",
        {},
        result,
        success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result


def list_blacklist() -> dict:
    """
    List all commands in the blacklist.

    Returns:
        A dictionary with status and the current blacklist.
    """
    t0 = time.perf_counter()
    result = {
        "status": "success",
        "blacklist": (
            globals_module.GLOBAL_BLACKLIST.copy() if globals_module.GLOBAL_BLACKLIST else []
        ),
        "count": len(globals_module.GLOBAL_BLACKLIST) if globals_module.GLOBAL_BLACKLIST else 0,
    }
    log_tool_call(
        "list_blacklist",
        {},
        result,
        success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result


def is_in_allowlist(command: str) -> dict:
    """
    Check if a command is in the allowlist.

    This is useful for checking command permissions before execution.
    The function checks if the base command (first word) matches any entry in the allowlist.

    Args:
        command: The command to check (e.g., "ls", "git status", "docker ps").

    Returns:
        A dictionary with status, whether the command is in the allowlist, and the matched entry if found.
    """
    t0 = time.perf_counter()
    # Extract base command
    cmd_parts = command.strip().split()
    if not cmd_parts:
        result = {
            "status": "error",
            "message": "Empty command",
            "in_allowlist": False,
        }
        log_tool_call(
            "is_in_allowlist",
            {"command": command},
            result,
            success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result

    base_cmd = cmd_parts[0]

    # Check if command is in allowlist
    in_allowlist = False
    matched_entry = None

    if globals_module.GLOBAL_ALLOWLIST:
        for allowed_cmd in globals_module.GLOBAL_ALLOWLIST:
            if allowed_cmd in base_cmd or base_cmd in allowed_cmd:
                in_allowlist = True
                matched_entry = allowed_cmd
                break

    result = {
        "status": "success",
        "command": command,
        "base_command": base_cmd,
        "in_allowlist": in_allowlist,
        "matched_entry": matched_entry,
    }
    log_tool_call(
        "is_in_allowlist",
        {"command": command},
        result,
        success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result


def is_in_blacklist(command: str) -> dict:
    """
    Check if a command is in the blacklist.

    This is useful for checking if a command is blocked before attempting execution.
    The function checks if the base command (first word) matches any entry in the blacklist.

    Args:
        command: The command to check (e.g., "rm", "dd if=/dev/zero", "format c:").

    Returns:
        A dictionary with status, whether the command is in the blacklist, and the matched entry if found.
    """
    t0 = time.perf_counter()
    # Extract base command
    cmd_parts = command.strip().split()
    if not cmd_parts:
        result = {
            "status": "error",
            "message": "Empty command",
            "in_blacklist": False,
        }
        log_tool_call(
            "is_in_blacklist",
            {"command": command},
            result,
            success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result

    base_cmd = cmd_parts[0]

    # Check if command is in blacklist
    in_blacklist = False
    matched_entry = None

    if globals_module.GLOBAL_BLACKLIST:
        for blacklisted in globals_module.GLOBAL_BLACKLIST:
            if blacklisted in base_cmd or base_cmd in blacklisted:
                in_blacklist = True
                matched_entry = blacklisted
                break

    result = {
        "status": "success",
        "command": command,
        "base_command": base_cmd,
        "in_blacklist": in_blacklist,
        "matched_entry": matched_entry,
    }
    log_tool_call(
        "is_in_blacklist",
        {"command": command},
        result,
        success=True,
        duration_seconds=time.perf_counter() - t0,
    )
    return result
