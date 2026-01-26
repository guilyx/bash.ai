"""Custom tools for Flourish agent."""

import os
import subprocess
from pathlib import Path
from typing import Any

from google.adk.tools import FunctionTool, ToolContext

from ..logging import log_terminal_error, log_terminal_output, log_tool_call

# Global variable for working directory
GLOBAL_CWD = os.getcwd()  # Default to current directory

# Global variables for allowlist/blacklist
GLOBAL_ALLOWLIST: list[str] | None = None
GLOBAL_BLACKLIST: list[str] | None = None


def set_allowlist_blacklist(allowlist: list[str] | None = None, blacklist: list[str] | None = None):
    """Set the global allowlist and blacklist for command validation.

    Args:
        allowlist: List of allowed commands
        blacklist: List of blacklisted commands
    """
    global GLOBAL_ALLOWLIST, GLOBAL_BLACKLIST
    GLOBAL_ALLOWLIST = allowlist
    GLOBAL_BLACKLIST = blacklist


def get_user() -> dict[str, Any]:
    """
    Get the current user information including username and home directory.

    This tool helps the agent understand the actual user context instead of using
    hardcoded paths like /home/user. Uses execute_bash to get user information.

    Returns:
        A dictionary with username, home directory, and current working directory.
    """
    # Get username using whoami command
    username_result = execute_bash("whoami")
    username = (
        username_result.get("stdout", "").strip()
        if username_result.get("status") == "success"
        else "unknown"
    )

    # Get home directory using echo $HOME
    home_result = execute_bash("echo $HOME")
    home_dir = (
        home_result.get("stdout", "").strip()
        if home_result.get("status") == "success"
        else str(Path.home())
    )

    # Get current working directory using pwd
    pwd_result = execute_bash("pwd")
    current_dir = (
        pwd_result.get("stdout", "").strip()
        if pwd_result.get("status") == "success"
        else GLOBAL_CWD
    )

    result: dict[str, Any] = {
        "username": username,
        "home_directory": home_dir,
        "current_working_directory": current_dir,
    }
    log_tool_call("get_user", {}, result, success=True)
    return result


def set_cwd(path: str) -> str:
    """
    Set the global working directory for bash commands.

    Args:
        path: The absolute path to use as the new working directory.

    Returns:
        A confirmation message.
    """
    global GLOBAL_CWD

    if not os.path.isdir(path):
        error_msg = f"Invalid directory: {path}"
        log_tool_call("set_cwd", {"path": path}, error_msg, success=False)
        raise ValueError(error_msg)

    GLOBAL_CWD = path
    result = f"Working directory set to: {GLOBAL_CWD}"
    log_tool_call("set_cwd", {"path": path}, result, success=True)
    return result


def execute_bash(cmd: str, tool_context: ToolContext | None = None) -> dict:
    """
    Run a bash command in the global working directory.

    This function checks allowlist/blacklist before execution.
    Commands not in the allowlist are automatically added to allowlist and executed.

    Args:
        cmd: The shell command to execute.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and output from the command execution.
    """
    global GLOBAL_CWD, GLOBAL_ALLOWLIST, GLOBAL_BLACKLIST

    # Extract base command for checking
    cmd_parts = cmd.strip().split()
    if not cmd_parts:
        return {"status": "error", "message": "Empty command"}

    base_cmd = cmd_parts[0]

    # SECURITY: Check blacklist FIRST - blacklist always takes precedence over allowlist
    # This ensures that allowlist can NEVER bypass blacklist restrictions
    if GLOBAL_BLACKLIST:
        for blacklisted in GLOBAL_BLACKLIST:
            if blacklisted in base_cmd or base_cmd in blacklisted:
                blocked_result: dict[str, Any] = {
                    "status": "blocked",
                    "message": f"Command '{base_cmd}' is blacklisted and cannot be executed",
                }
                log_tool_call("execute_bash", {"cmd": cmd}, blocked_result, success=False)
                return blocked_result

    # Check if command is in allowlist (only after blacklist check passes)
    in_allowlist = False
    if GLOBAL_ALLOWLIST:
        for allowed_cmd in GLOBAL_ALLOWLIST:
            if allowed_cmd in base_cmd or base_cmd in allowed_cmd:
                in_allowlist = True
                break

    # If not in allowlist, automatically add it and continue
    if not in_allowlist:
        # Automatically add to allowlist
        if GLOBAL_ALLOWLIST is None:
            GLOBAL_ALLOWLIST = []
        if base_cmd not in GLOBAL_ALLOWLIST:
            GLOBAL_ALLOWLIST.append(base_cmd)
            # Update config manager if available
            try:
                from ..config.config_manager import ConfigManager

                config_manager = ConfigManager()
                config_manager.add_to_allowlist(base_cmd)
            except Exception:
                pass  # Config manager might not be available

    # SECURITY: Final blacklist check before execution (defense in depth)
    # This ensures that even if a command was added to allowlist after initial check,
    # it will still be blocked if it's in the blacklist
    if GLOBAL_BLACKLIST:
        for blacklisted in GLOBAL_BLACKLIST:
            if blacklisted in base_cmd or base_cmd in blacklisted:
                blocked_result: dict[str, Any] = {
                    "status": "blocked",
                    "message": f"Command '{base_cmd}' is blacklisted and cannot be executed",
                }
                log_tool_call("execute_bash", {"cmd": cmd}, blocked_result, success=False)
                return blocked_result

    # Execute the command
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            cwd=GLOBAL_CWD,
        )
        stdout, stderr = process.communicate()

        result: dict[str, Any] = {
            "status": "success" if process.returncode == 0 else "error",
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": process.returncode,
            "cmd": cmd,
        }

        # Log tool call to conversation log
        log_tool_call(
            "execute_bash",
            {"cmd": cmd, "cwd": str(GLOBAL_CWD)},
            result,
            success=(process.returncode == 0),
        )

        # Log terminal output to terminal log
        log_terminal_output(
            command=cmd,
            stdout=stdout,
            stderr=stderr,
            exit_code=process.returncode,
            cwd=str(GLOBAL_CWD),
        )

        return result
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"Error executing command: {e}",
            "cmd": cmd,
        }
        # Log tool call to conversation log
        log_tool_call("execute_bash", {"cmd": cmd}, error_result, success=False)
        # Log terminal error to terminal log
        log_terminal_error(command=cmd, error=str(e), cwd=str(GLOBAL_CWD))
        return error_result


def add_to_allowlist(command: str, tool_context: ToolContext | None = None) -> dict:
    """
    Add a command to the allowlist.

    Args:
        command: The base command to add (e.g., "ls", "git", "docker", "npm"). Extract from full command if needed.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status, message, and updated allowlist.
    """

    # Add to allowlist
    global GLOBAL_ALLOWLIST
    if GLOBAL_ALLOWLIST is None:
        GLOBAL_ALLOWLIST = []
    if command not in GLOBAL_ALLOWLIST:
        GLOBAL_ALLOWLIST.append(command)
        # Update config manager if available
        try:
            from ..config.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.add_to_allowlist(command)
        except Exception:
            pass  # Config manager might not be available

    result = {
        "status": "success",
        "message": f"Added '{command}' to allowlist",
        "allowlist": GLOBAL_ALLOWLIST.copy(),
    }
    log_tool_call("add_to_allowlist", {"command": command}, result, success=True)
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

    # Remove from allowlist
    global GLOBAL_ALLOWLIST
    if GLOBAL_ALLOWLIST and command in GLOBAL_ALLOWLIST:
        GLOBAL_ALLOWLIST.remove(command)
        # Update config manager if available
        try:
            from ..config.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.remove_from_allowlist(command)
        except Exception:
            pass

    result = {
        "status": "success",
        "message": f"Removed '{command}' from allowlist",
        "allowlist": GLOBAL_ALLOWLIST.copy() if GLOBAL_ALLOWLIST else [],
    }
    log_tool_call("remove_from_allowlist", {"command": command}, result, success=True)
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

    # Add to blacklist
    global GLOBAL_BLACKLIST
    if GLOBAL_BLACKLIST is None:
        GLOBAL_BLACKLIST = []
    if command not in GLOBAL_BLACKLIST:
        GLOBAL_BLACKLIST.append(command)
        # Update config manager if available
        try:
            from ..config.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.add_to_blacklist(command)
        except Exception:
            pass

    result = {
        "status": "success",
        "message": f"Added '{command}' to blacklist",
        "blacklist": GLOBAL_BLACKLIST.copy(),
    }
    log_tool_call("add_to_blacklist", {"command": command}, result, success=True)
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

    # Remove from blacklist
    global GLOBAL_BLACKLIST
    if GLOBAL_BLACKLIST and command in GLOBAL_BLACKLIST:
        GLOBAL_BLACKLIST.remove(command)
        # Update config manager if available
        try:
            from ..config.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.remove_from_blacklist(command)
        except Exception:
            pass

    result = {
        "status": "success",
        "message": f"Removed '{command}' from blacklist",
        "blacklist": GLOBAL_BLACKLIST.copy() if GLOBAL_BLACKLIST else [],
    }
    log_tool_call("remove_from_blacklist", {"command": command}, result, success=True)
    return result


def list_allowlist() -> dict:
    """
    List all commands in the allowlist.

    Returns:
        A dictionary with status and the current allowlist.
    """
    global GLOBAL_ALLOWLIST

    result = {
        "status": "success",
        "allowlist": GLOBAL_ALLOWLIST.copy() if GLOBAL_ALLOWLIST else [],
        "count": len(GLOBAL_ALLOWLIST) if GLOBAL_ALLOWLIST else 0,
    }
    log_tool_call("list_allowlist", {}, result, success=True)
    return result


def list_blacklist() -> dict:
    """
    List all commands in the blacklist.

    Returns:
        A dictionary with status and the current blacklist.
    """
    global GLOBAL_BLACKLIST

    result = {
        "status": "success",
        "blacklist": GLOBAL_BLACKLIST.copy() if GLOBAL_BLACKLIST else [],
        "count": len(GLOBAL_BLACKLIST) if GLOBAL_BLACKLIST else 0,
    }
    log_tool_call("list_blacklist", {}, result, success=True)
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
    global GLOBAL_ALLOWLIST

    # Extract base command
    cmd_parts = command.strip().split()
    if not cmd_parts:
        result = {
            "status": "error",
            "message": "Empty command",
            "in_allowlist": False,
        }
        log_tool_call("is_in_allowlist", {"command": command}, result, success=False)
        return result

    base_cmd = cmd_parts[0]

    # Check if command is in allowlist
    in_allowlist = False
    matched_entry = None

    if GLOBAL_ALLOWLIST:
        for allowed_cmd in GLOBAL_ALLOWLIST:
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
    log_tool_call("is_in_allowlist", {"command": command}, result, success=True)
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
    global GLOBAL_BLACKLIST

    # Extract base command
    cmd_parts = command.strip().split()
    if not cmd_parts:
        result = {
            "status": "error",
            "message": "Empty command",
            "in_blacklist": False,
        }
        log_tool_call("is_in_blacklist", {"command": command}, result, success=False)
        return result

    base_cmd = cmd_parts[0]

    # Check if command is in blacklist
    in_blacklist = False
    matched_entry = None

    if GLOBAL_BLACKLIST:
        for blacklisted in GLOBAL_BLACKLIST:
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
    log_tool_call("is_in_blacklist", {"command": command}, result, success=True)
    return result


def get_bash_tools(allowlist: list[str] | None = None, blacklist: list[str] | None = None):
    """Get bash execution tools for the agent (Google ADK format).

    Args:
        allowlist: Optional list of allowed commands
        blacklist: Optional list of blacklisted commands

    Returns:
        List of FunctionTool objects for bash execution and management.
    """
    # Set global allowlist/blacklist
    set_allowlist_blacklist(allowlist, blacklist)

    # Wrap tools - no confirmations required, all tools execute directly
    tools = [
        get_user,
        set_cwd,
        FunctionTool(execute_bash, require_confirmation=False),
        FunctionTool(add_to_allowlist, require_confirmation=False),
        FunctionTool(remove_from_allowlist, require_confirmation=False),
        FunctionTool(add_to_blacklist, require_confirmation=False),
        FunctionTool(remove_from_blacklist, require_confirmation=False),
        list_allowlist,
        list_blacklist,
        is_in_allowlist,
        is_in_blacklist,
    ]

    return tools
