"""Tools module for Flourish - organized by skills."""

from .base import BaseSkill, FunctionToolWrapper, Skill, SkillRegistry, Tool
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
from .registry import get_registry
from .ros2 import (
    ros2_action_info,
    ros2_action_list,
    ros2_bag_compress,
    ros2_bag_decompress,
    ros2_bag_info,
    ros2_bag_play,
    ros2_bag_record,
    ros2_bag_reindex,
    ros2_bag_validate,
    ros2_interface_list,
    ros2_interface_show,
    ros2_node_info,
    ros2_node_list,
    ros2_param_get,
    ros2_param_list,
    ros2_param_set,
    ros2_pkg_list,
    ros2_pkg_prefix,
    ros2_service_call,
    ros2_service_list,
    ros2_service_type,
    ros2_topic_echo,
    ros2_topic_hz,
    ros2_topic_info,
    ros2_topic_list,
    ros2_topic_type,
)
from .system import get_current_datetime
from .tool_manager import (
    disable_tool,
    enable_tool,
    get_available_tools,
    list_enabled_tools,
)

__all__ = [
    # Base classes
    "Skill",
    "BaseSkill",
    "SkillRegistry",
    "Tool",
    "FunctionToolWrapper",
    "get_registry",
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
    # Tool manager tools
    "get_available_tools",
    "list_enabled_tools",
    "enable_tool",
    "disable_tool",
    # ROS2 tools
    "ros2_topic_list",
    "ros2_topic_echo",
    "ros2_topic_info",
    "ros2_topic_hz",
    "ros2_topic_type",
    "ros2_service_list",
    "ros2_service_type",
    "ros2_service_call",
    "ros2_action_list",
    "ros2_action_info",
    "ros2_node_list",
    "ros2_node_info",
    "ros2_param_list",
    "ros2_param_get",
    "ros2_param_set",
    "ros2_interface_list",
    "ros2_interface_show",
    "ros2_pkg_list",
    "ros2_pkg_prefix",
    "ros2_bag_record",
    "ros2_bag_play",
    "ros2_bag_info",
    "ros2_bag_reindex",
    "ros2_bag_compress",
    "ros2_bag_decompress",
    "ros2_bag_validate",
    # Main function
    "get_bash_tools",
    "get_enabled_tool_names",
]

# Legacy tool registry removed - use get_registry() instead


def get_enabled_tool_names() -> list[str]:
    """Get enabled tool names from config (derived from enabled skills).

    Returns:
        Sorted list of tool names from all enabled skills.
    """
    try:
        from ..config.config_manager import ConfigManager

        config_manager = ConfigManager()
        enabled_skills = config_manager.get_enabled_skills()
    except Exception:
        # Fallback to all tools if config can't be loaded
        registry = get_registry()
        return registry.get_all_tool_names()

    registry = get_registry()
    return registry.get_tool_names_for_skills(enabled_skills)


def get_bash_tools(
    allowlist: list[str] | None = None,
    blacklist: list[str] | None = None,
    enabled_tools: list[str] | None = None,
):
    """Get tools for the agent (Google ADK format).

    Args:
        allowlist: Optional list of allowed commands
        blacklist: Optional list of blacklisted commands
        enabled_tools: Optional list of enabled tool names. If None, loads from config.

    Returns:
        List of FunctionTool objects for agent use.
    """
    # Set global allowlist/blacklist
    set_allowlist_blacklist(allowlist, blacklist)

    # Load enabled tools from config (derived from enabled skills) if not provided
    if enabled_tools is None:
        enabled_tools = get_enabled_tool_names()

    # Use the registry to get enabled tools
    registry = get_registry()
    return registry.get_enabled_tools(enabled_tools)
