"""Bash execution tools for running shell commands."""

import os
import subprocess
from pathlib import Path
from typing import Any

from google.adk.tools import ToolContext

from ...logging import log_terminal_error, log_terminal_output, log_tool_call
from .. import globals as globals_module


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
        else globals_module.GLOBAL_CWD
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
    if not os.path.isdir(path):
        error_msg = f"Invalid directory: {path}"
        log_tool_call("set_cwd", {"path": path}, error_msg, success=False)
        raise ValueError(error_msg)

    globals_module.GLOBAL_CWD = path
    result = f"Working directory set to: {globals_module.GLOBAL_CWD}"
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
    # Extract base command for checking
    cmd_parts = cmd.strip().split()
    if not cmd_parts:
        return {"status": "error", "message": "Empty command"}

    base_cmd = cmd_parts[0]

    # SECURITY: Check blacklist FIRST - blacklist always takes precedence over allowlist
    # This ensures that allowlist can NEVER bypass blacklist restrictions
    if globals_module.GLOBAL_BLACKLIST:
        for blacklisted in globals_module.GLOBAL_BLACKLIST:
            if blacklisted in base_cmd or base_cmd in blacklisted:
                blocked_result: dict[str, Any] = {
                    "status": "blocked",
                    "message": f"Command '{base_cmd}' is blacklisted and cannot be executed",
                }
                log_tool_call("execute_bash", {"cmd": cmd}, blocked_result, success=False)
                return blocked_result

    # Check if command is in allowlist (only after blacklist check passes)
    in_allowlist = False
    if globals_module.GLOBAL_ALLOWLIST:
        for allowed_cmd in globals_module.GLOBAL_ALLOWLIST:
            if allowed_cmd in base_cmd or base_cmd in allowed_cmd:
                in_allowlist = True
                break

    # If not in allowlist, automatically add it and continue
    if not in_allowlist:
        # Automatically add to allowlist
        if globals_module.GLOBAL_ALLOWLIST is None:
            globals_module.GLOBAL_ALLOWLIST = []
        if base_cmd not in globals_module.GLOBAL_ALLOWLIST:
            globals_module.GLOBAL_ALLOWLIST.append(base_cmd)
            # Update config manager if available
            try:
                from ...config.config_manager import ConfigManager

                config_manager = ConfigManager()
                config_manager.add_to_allowlist(base_cmd)
            except Exception:
                pass  # Config manager might not be available

    # SECURITY: Final blacklist check before execution (defense in depth)
    # This ensures that even if a command was added to allowlist after initial check,
    # it will still be blocked if it's in the blacklist
    if globals_module.GLOBAL_BLACKLIST:
        for blacklisted in globals_module.GLOBAL_BLACKLIST:
            if blacklisted in base_cmd or base_cmd in blacklisted:
                final_blocked_result: dict[str, Any] = {
                    "status": "blocked",
                    "message": f"Command '{base_cmd}' is blacklisted and cannot be executed",
                }
                log_tool_call("execute_bash", {"cmd": cmd}, final_blocked_result, success=False)
                return final_blocked_result

    # Execute the command
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            cwd=globals_module.GLOBAL_CWD,
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
            {"cmd": cmd, "cwd": str(globals_module.GLOBAL_CWD)},
            result,
            success=(process.returncode == 0),
        )

        # Log terminal output to terminal log
        log_terminal_output(
            command=cmd,
            stdout=stdout,
            stderr=stderr,
            exit_code=process.returncode,
            cwd=str(globals_module.GLOBAL_CWD),
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
        log_terminal_error(command=cmd, error=str(e), cwd=str(globals_module.GLOBAL_CWD))
        return error_result
