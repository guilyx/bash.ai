"""Custom tools for bash.ai agent."""

import os
import subprocess
from typing import Any

from google.adk.tools import FunctionTool, ToolContext

from ..logging import log_tool_call

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
    Commands not in the allowlist require user confirmation.

    Args:
        cmd: The shell command to execute.
        tool_context: Tool context for confirmation (automatically provided by ADK).

    Returns:
        A dictionary with status and output from the command execution.
    """
    global GLOBAL_CWD, GLOBAL_ALLOWLIST, GLOBAL_BLACKLIST

    # Extract base command for checking
    cmd_parts = cmd.strip().split()
    if not cmd_parts:
        return {"status": "error", "message": "Empty command"}

    base_cmd = cmd_parts[0]

    # Check blacklist first (always blocked)
    if GLOBAL_BLACKLIST:
        for blacklisted in GLOBAL_BLACKLIST:
            if blacklisted in base_cmd or base_cmd in blacklisted:
                blocked_result: dict[str, Any] = {
                    "status": "blocked",
                    "message": f"Command '{base_cmd}' is blacklisted",
                }
                log_tool_call("execute_bash", {"cmd": cmd}, blocked_result, success=False)
                return blocked_result

    # Check if command is in allowlist
    in_allowlist = False
    if GLOBAL_ALLOWLIST:
        for allowed_cmd in GLOBAL_ALLOWLIST:
            if allowed_cmd in base_cmd or base_cmd in allowed_cmd:
                in_allowlist = True
                break

    # If not in allowlist, require confirmation
    if not in_allowlist:
        if tool_context:
            tool_confirmation = tool_context.tool_confirmation
            if not tool_confirmation:
                # Request confirmation and suggest adding to allowlist
                tool_context.request_confirmation(
                    hint=(
                        f"Command '{base_cmd}' is not in the allowlist. "
                        f"Do you want to execute: {cmd}?\n\n"
                        f"To avoid confirmation prompts in the future, you can add this command to the allowlist "
                        f"using the 'add_to_allowlist' tool. This will allow the agent to execute '{base_cmd}' "
                        f"without requiring confirmation.\n\n"
                        f"Respond with 'confirmed: true' to proceed with execution, or 'confirmed: false' to cancel."
                    ),
                    payload={"confirmed": False, "cmd": cmd, "suggest_add_to_allowlist": True},
                )
                return {
                    "status": "pending_confirmation",
                    "message": (
                        f"Waiting for confirmation to execute: {cmd}\n"
                        f"Tip: Use 'add_to_allowlist' tool to add '{base_cmd}' to allowlist "
                        f"and avoid confirmation prompts in the future."
                    ),
                }

            # Check confirmation response
            confirmed = tool_confirmation.payload.get("confirmed", False)
            if not confirmed:
                cancelled_result: dict[str, Any] = {
                    "status": "cancelled",
                    "message": f"Execution of '{cmd}' was cancelled by user",
                }
                log_tool_call("execute_bash", {"cmd": cmd}, cancelled_result, success=False)
                return cancelled_result
        else:
            # No tool context (LiteLLM mode) - return pending confirmation
            return {
                "status": "pending_confirmation",
                "message": (
                    f"Command '{base_cmd}' is not in the allowlist. "
                    f"Use 'add_to_allowlist' tool to add '{base_cmd}' to allowlist, then retry."
                ),
            }

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

        log_tool_call(
            "execute_bash",
            {"cmd": cmd, "cwd": str(GLOBAL_CWD)},
            result,
            success=(process.returncode == 0),
        )
        return result
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"Error executing command: {e}",
            "cmd": cmd,
        }
        log_tool_call("execute_bash", {"cmd": cmd}, error_result, success=False)
        return error_result


def add_to_allowlist(command: str, tool_context: ToolContext | None = None) -> dict:
    """
    Add a command to the allowlist to avoid future confirmation prompts.

    **MANDATORY USE**: Call this tool automatically when `execute_bash` returns status "pending_confirmation".
    Don't ask the user - just call this tool immediately, then retry the command.

    When to use (automatic, don't ask):
    - When `execute_bash` returns status "pending_confirmation" - call this immediately
    - When you need to use a command multiple times in a workflow
    - When a command fails due to allowlist restrictions but is safe to use

    Workflow:
    1. Call `execute_bash("some_command")`
    2. If it returns "pending_confirmation", immediately call `add_to_allowlist("base_command")`
    3. After confirmation completes, call `execute_bash("some_command")` again
    4. Command will now execute without confirmation

    The system will handle the confirmation automatically. After adding, the command
    can be executed without confirmation prompts, improving workflow efficiency.

    Args:
        command: The base command to add (e.g., "ls", "git", "docker", "npm"). Extract from full command if needed.
        tool_context: Tool context for confirmation (automatically provided by ADK).

    Returns:
        A dictionary with status, message, and updated allowlist.
    """
    if tool_context:
        tool_confirmation = tool_context.tool_confirmation
        if not tool_confirmation:
            # Request confirmation
            tool_context.request_confirmation(
                hint=(
                    f"Do you want to add '{command}' to the allowlist?\n"
                    f"This will allow the agent to execute this command without confirmation in the future."
                ),
                payload={"confirmed": False, "command": command},
            )
            return {
                "status": "pending_confirmation",
                "message": f"Waiting for confirmation to add '{command}' to allowlist",
            }

        # Check confirmation response
        confirmed = tool_confirmation.payload.get("confirmed", False)
        if not confirmed:
            return {
                "status": "cancelled",
                "message": f"Adding '{command}' to allowlist was cancelled",
            }
    # If no tool_context (LiteLLM mode), auto-confirm

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
    Remove a command from the allowlist. Requires confirmation.

    Args:
        command: The command to remove from the allowlist.
        tool_context: Tool context for confirmation (automatically provided by ADK).

    Returns:
        A dictionary with status and message.
    """
    if tool_context:
        tool_confirmation = tool_context.tool_confirmation
        if not tool_confirmation:
            # Request confirmation
            tool_context.request_confirmation(
                hint=(
                    f"Do you want to remove '{command}' from the allowlist?\n"
                    f"This will require confirmation for this command in the future."
                ),
                payload={"confirmed": False, "command": command},
            )
            return {
                "status": "pending_confirmation",
                "message": f"Waiting for confirmation to remove '{command}' from allowlist",
            }

        # Check confirmation response
        confirmed = tool_confirmation.payload.get("confirmed", False)
        if not confirmed:
            return {
                "status": "cancelled",
                "message": f"Removing '{command}' from allowlist was cancelled",
            }
    # If no tool_context (LiteLLM mode), auto-confirm

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
        tool_context: Tool context for confirmation (automatically provided by ADK).

    Returns:
        A dictionary with status, message, and updated blacklist.
    """
    if tool_context:
        tool_confirmation = tool_context.tool_confirmation
        if not tool_confirmation:
            # Request confirmation
            tool_context.request_confirmation(
                hint=(
                    f"Do you want to add '{command}' to the blacklist?\n"
                    f"This will permanently block this command from being executed."
                ),
                payload={"confirmed": False, "command": command},
            )
            return {
                "status": "pending_confirmation",
                "message": f"Waiting for confirmation to add '{command}' to blacklist",
            }

        # Check confirmation response
        confirmed = tool_confirmation.payload.get("confirmed", False)
        if not confirmed:
            return {
                "status": "cancelled",
                "message": f"Adding '{command}' to blacklist was cancelled",
            }
    # If no tool_context (LiteLLM mode), auto-confirm

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
    Remove a command from the blacklist. Requires confirmation.

    Args:
        command: The command to remove from the blacklist.
        tool_context: Tool context for confirmation (automatically provided by ADK).

    Returns:
        A dictionary with status and message.
    """
    if tool_context:
        tool_confirmation = tool_context.tool_confirmation
        if not tool_confirmation:
            # Request confirmation
            tool_context.request_confirmation(
                hint=(
                    f"Do you want to remove '{command}' from the blacklist?\n"
                    f"This will allow this command to be executed again (subject to allowlist restrictions)."
                ),
                payload={"confirmed": False, "command": command},
            )
            return {
                "status": "pending_confirmation",
                "message": f"Waiting for confirmation to remove '{command}' from blacklist",
            }

        # Check confirmation response
        confirmed = tool_confirmation.payload.get("confirmed", False)
        if not confirmed:
            return {
                "status": "cancelled",
                "message": f"Removing '{command}' from blacklist was cancelled",
            }
    # If no tool_context (LiteLLM mode), auto-confirm

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

    # Wrap tools appropriately
    # execute_bash handles confirmation internally for non-allowlisted commands
    # Management tools always require confirmation
    # List tools don't require confirmation (read-only)
    tools = [
        set_cwd,  # No confirmation needed for directory changes
        FunctionTool(execute_bash),  # Confirmation handled internally
        FunctionTool(add_to_allowlist, require_confirmation=True),
        FunctionTool(remove_from_allowlist, require_confirmation=True),
        FunctionTool(add_to_blacklist, require_confirmation=True),
        FunctionTool(remove_from_blacklist, require_confirmation=True),
        list_allowlist,  # Read-only, no confirmation needed
        list_blacklist,  # Read-only, no confirmation needed
    ]

    return tools


