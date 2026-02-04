"""Tool manager tools for managing enabled tools (via skills)."""

import time
from typing import Any

from google.adk.tools import ToolContext

from ...config.config_manager import ConfigManager
from ...logging import log_tool_call


def _get_enabled_tool_names() -> list[str]:
    """Get enabled tool names from config (derived from enabled skills). Lazy import avoids circular import."""
    from ..registry import get_registry

    config_manager = ConfigManager()
    enabled_skills = config_manager.get_enabled_skills()
    return get_registry().get_tool_names_for_skills(enabled_skills)


def get_available_tools() -> dict[str, Any]:
    """
    Get a list of all available tools in the system.

    Returns:
        A dictionary with status and list of available tools with their descriptions.
    """
    t0 = time.perf_counter()
    try:
        from ..registry import get_registry

        registry = get_registry()
        tools_info = registry.get_all_tools_info()

        # Convert to simple name -> description format for backward compatibility
        available_tools = {name: info["description"] for name, info in tools_info.items() if info}

        result = {
            "status": "success",
            "available_tools": available_tools,
            "count": len(available_tools),
        }
        log_tool_call(
            "get_available_tools",
            {},
            result,
            success=True,
            duration_seconds=time.perf_counter() - t0,
        )
        return result
    except Exception as e:
        # Fallback to empty dict if registry fails
        result = {
            "status": "error",
            "message": f"Failed to get available tools: {e}",
            "available_tools": {},
            "count": 0,
        }
        log_tool_call(
            "get_available_tools",
            {},
            result,
            success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result


def list_enabled_tools(tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    List all currently enabled tools (derived from enabled skills).

    Returns:
        A dictionary with status and list of enabled tools.
    """
    t0 = time.perf_counter()
    try:
        enabled_tools = _get_enabled_tool_names()

        result = {
            "status": "success",
            "enabled_tools": enabled_tools,
            "count": len(enabled_tools),
        }
        log_tool_call(
            "list_enabled_tools",
            {},
            result,
            success=True,
            duration_seconds=time.perf_counter() - t0,
        )
        return result
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to list enabled tools: {e}",
        }
        log_tool_call(
            "list_enabled_tools",
            {},
            result,
            success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result


def enable_tool(tool_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Enable a tool by enabling the skill that provides it.

    Args:
        tool_name: The name of the tool to enable (e.g., "ros2_topic_list", "execute_bash").
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status, message, and updated enabled tools list.
    """
    t0 = time.perf_counter()
    try:
        from ..registry import get_registry

        registry = get_registry()
        skill_name = registry.get_skill_for_tool(tool_name)
        if skill_name is None:
            result = {
                "status": "error",
                "message": f"Unknown tool '{tool_name}'",
            }
            log_tool_call(
                "enable_tool",
                {"tool_name": tool_name},
                result,
                success=False,
                duration_seconds=time.perf_counter() - t0,
            )
            return result

        config_manager = ConfigManager()
        config_manager.add_skill(skill_name)
        enabled_tools = _get_enabled_tool_names()

        result = {
            "status": "success",
            "message": f"Tool '{tool_name}' enabled (skill '{skill_name}')",
            "enabled_tools": enabled_tools,
        }
        log_tool_call(
            "enable_tool",
            {"tool_name": tool_name},
            result,
            success=True,
            duration_seconds=time.perf_counter() - t0,
        )
        return result
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to enable tool '{tool_name}': {e}",
        }
        log_tool_call(
            "enable_tool",
            {"tool_name": tool_name},
            result,
            success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result


def disable_tool(tool_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Disable a tool by disabling the skill that provides it.

    Args:
        tool_name: The name of the tool to disable (e.g., "ros2_topic_list", "execute_bash").
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status, message, and updated enabled tools list.
    """
    t0 = time.perf_counter()
    try:
        from ..registry import get_registry

        registry = get_registry()
        skill_name = registry.get_skill_for_tool(tool_name)
        if skill_name is None:
            result = {
                "status": "error",
                "message": f"Unknown tool '{tool_name}'",
            }
            log_tool_call(
                "disable_tool",
                {"tool_name": tool_name},
                result,
                success=False,
                duration_seconds=time.perf_counter() - t0,
            )
            return result

        config_manager = ConfigManager()
        config_manager.remove_skill(skill_name)
        enabled_tools = _get_enabled_tool_names()

        result = {
            "status": "success",
            "message": f"Tool '{tool_name}' disabled (skill '{skill_name}')",
            "enabled_tools": enabled_tools,
        }
        log_tool_call(
            "disable_tool",
            {"tool_name": tool_name},
            result,
            success=True,
            duration_seconds=time.perf_counter() - t0,
        )
        return result
    except Exception as e:
        result = {
            "status": "error",
            "message": f"Failed to disable tool '{tool_name}': {e}",
        }
        log_tool_call(
            "disable_tool",
            {"tool_name": tool_name},
            result,
            success=False,
            duration_seconds=time.perf_counter() - t0,
        )
        return result
