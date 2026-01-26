"""Tools module for Flourish - organized by context."""

from google.adk.tools import FunctionTool

from .bash import execute_bash, get_user, set_cwd
from .config import (
    add_to_allowlist,
    add_to_blacklist,
    is_in_allowlist,
    is_in_blacklist,
    list_allowlist,
    list_blacklist,
    remove_from_allowlist,
    remove_from_blacklist,
    set_allowlist_blacklist,
)
from .globals import GLOBAL_ALLOWLIST, GLOBAL_BLACKLIST, GLOBAL_CWD
from .history import read_bash_history, read_conversation_history
from .system import get_current_datetime

__all__ = [
    # Globals
    "GLOBAL_CWD",
    "GLOBAL_ALLOWLIST",
    "GLOBAL_BLACKLIST",
    # Configuration
    "set_allowlist_blacklist",
    # Bash tools
    "execute_bash",
    "get_user",
    "set_cwd",
    # Config tools
    "add_to_allowlist",
    "remove_from_allowlist",
    "add_to_blacklist",
    "remove_from_blacklist",
    "list_allowlist",
    "list_blacklist",
    "is_in_allowlist",
    "is_in_blacklist",
    # History tools
    "read_bash_history",
    "read_conversation_history",
    # System tools
    "get_current_datetime",
    # Main function
    "get_bash_tools",
]


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
        read_bash_history,
        read_conversation_history,
        get_current_datetime,
    ]

    return tools
