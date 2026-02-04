"""Tool manager skill."""

from ..base import BaseSkill, FunctionToolWrapper
from .tool_manager_tools import disable_tool, enable_tool, get_available_tools, list_enabled_tools


class ToolManagerSkill(BaseSkill):
    """Tool manager skill."""

    def __init__(self):
        """Initialize the tool manager skill."""
        super().__init__(
            name="tool_manager",
            description="Tool management and configuration",
            tools=[
                FunctionToolWrapper(
                    "get_available_tools", get_available_tools, "List all available tools"
                ),
                FunctionToolWrapper(
                    "list_enabled_tools", list_enabled_tools, "List currently enabled tools"
                ),
                FunctionToolWrapper("enable_tool", enable_tool, "Enable a tool"),
                FunctionToolWrapper("disable_tool", disable_tool, "Disable a tool"),
            ],
        )
