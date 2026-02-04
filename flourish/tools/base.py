"""Base skill and tool system for Flourish."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from google.adk.tools import FunctionTool


class Tool(ABC):
    """Base class for individual tools within a skill.

    A tool is a function that the AI agent can call. Each tool should:
    1. Have a unique name (lowercase with underscores)
    2. Have a description
    3. Optionally specify if it requires confirmation
    4. Provide the actual function to execute
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool name (lowercase with underscores).

        Returns:
            Tool name as a string
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what the tool does.

        Returns:
            Tool description as a string
        """
        raise NotImplementedError

    @property
    def requires_confirmation(self) -> bool:
        """Return whether this tool requires user confirmation before execution.

        Returns:
            True if confirmation is required, False otherwise
        """
        return False

    @abstractmethod
    def get_function(self) -> Callable:
        """Return the actual function that implements this tool.

        Returns:
            The callable function
        """
        raise NotImplementedError

    def to_function_tool(self) -> FunctionTool:
        """Convert this tool to a Google ADK FunctionTool.

        Returns:
            FunctionTool instance ready for use with the agent
        """
        return FunctionTool(
            self.get_function(),
            require_confirmation=self.requires_confirmation,
        )


class FunctionToolWrapper(Tool):
    """Wrapper for existing function-based tools.

    This allows existing functions to be registered as tools without
    requiring them to be refactored into Tool classes.
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        description: str,
        requires_confirmation: bool = False,
    ):
        """Initialize a function tool wrapper.

        Args:
            name: Tool name (lowercase with underscores)
            func: The function to wrap
            description: Description of what the tool does
            requires_confirmation: Whether this tool requires confirmation
        """
        self._name = name
        self._func = func
        self._description = description
        self._requires_confirmation = requires_confirmation

    @property
    def name(self) -> str:
        """Return the tool name."""
        return self._name

    @property
    def description(self) -> str:
        """Return the tool description."""
        return self._description

    @property
    def requires_confirmation(self) -> bool:
        """Return whether confirmation is required."""
        return self._requires_confirmation

    def get_function(self) -> Callable:
        """Return the wrapped function."""
        return self._func


class Skill(ABC):
    """Base class for skills.

    A skill is a collection of related tools. Each folder in the tools directory
    represents a skill (e.g., bash skill, config skill, ros2 skill).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the skill name (lowercase with underscores).

        Returns:
            Skill name as a string
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what this skill provides.

        Returns:
            Skill description as a string
        """
        raise NotImplementedError

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """Return all tools provided by this skill.

        Returns:
            List of Tool instances
        """
        raise NotImplementedError

    def get_tool(self, tool_name: str) -> Tool | None:
        """Get a specific tool by name.

        Args:
            tool_name: Name of the tool to get

        Returns:
            Tool instance if found, None otherwise
        """
        for tool in self.get_tools():
            if tool.name == tool_name:
                return tool
        return None


class BaseSkill(Skill):
    """Base implementation for skills that makes it easy to create new skills.

    This class provides a simple way to create skills by just providing:
    - A name
    - A description
    - A list of tools

    Example:
        class MySkill(BaseSkill):
            def __init__(self):
                super().__init__(
                    name="my_skill",
                    description="My skill description",
                    tools=[
                        FunctionToolWrapper("tool1", func1, "Tool 1 description"),
                        FunctionToolWrapper("tool2", func2, "Tool 2 description"),
                    ]
                )
    """

    def __init__(
        self,
        name: str,
        description: str,
        tools: list[Tool],
    ):
        """Initialize a base skill.

        Args:
            name: Skill name (lowercase with underscores)
            description: Description of what this skill provides
            tools: List of Tool instances this skill provides
        """
        self._name = name
        self._description = description
        self._tools = tools

    @property
    def name(self) -> str:
        """Return the skill name."""
        return self._name

    @property
    def description(self) -> str:
        """Return the skill description."""
        return self._description

    def get_tools(self) -> list[Tool]:
        """Return all tools provided by this skill."""
        return self._tools


class SkillRegistry:
    """Registry for managing skills and their tools."""

    def __init__(self):
        """Initialize the skill registry."""
        self._skills: dict[str, Skill] = {}
        self._tools: dict[str, Tool] = {}  # Flat registry of all tools by name

    def register(self, skill: Skill):
        """Register a skill in the registry.

        Args:
            skill: The skill to register

        Raises:
            ValueError: If a skill with the same name is already registered
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered")
        self._skills[skill.name] = skill

        # Register all tools from this skill
        for tool in skill.get_tools():
            if tool.name in self._tools:
                raise ValueError(
                    f"Tool '{tool.name}' is already registered (from skill '{skill.name}')"
                )
            self._tools[tool.name] = tool

    def get_skill(self, name: str) -> Skill | None:
        """Get a skill by name.

        Args:
            name: Skill name

        Returns:
            The skill if found, None otherwise
        """
        return self._skills.get(name)

    def get_all_skills(self) -> dict[str, Skill]:
        """Get all registered skills.

        Returns:
            Dictionary mapping skill names to Skill instances
        """
        return self._skills.copy()

    def get_all_skill_names(self) -> list[str]:
        """Get all registered skill names.

        Returns:
            List of skill names
        """
        return list(self._skills.keys())

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            The tool if found, None otherwise
        """
        return self._tools.get(name)

    def get_all_tools(self) -> dict[str, Tool]:
        """Get all registered tools.

        Returns:
            Dictionary mapping tool names to Tool instances
        """
        return self._tools.copy()

    def get_all_tool_names(self) -> list[str]:
        """Get all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_tools_by_skill(self, skill_name: str) -> dict[str, Tool]:
        """Get all tools from a specific skill.

        Args:
            skill_name: Skill name

        Returns:
            Dictionary mapping tool names to Tool instances from that skill
        """
        skill = self._skills.get(skill_name)
        if skill:
            return {tool.name: tool for tool in skill.get_tools()}
        return {}

    def get_tool_names_for_skills(self, skill_names: list[str]) -> list[str]:
        """Get tool names from the given skills.

        Args:
            skill_names: List of skill names to include.

        Returns:
            Sorted list of tool names from those skills (no duplicates).
        """
        names: set[str] = set()
        for skill_name in skill_names:
            skill = self._skills.get(skill_name)
            if skill:
                for tool in skill.get_tools():
                    names.add(tool.name)
        return sorted(names)

    def get_skill_for_tool(self, tool_name: str) -> str | None:
        """Get the name of the skill that provides the given tool.

        Args:
            tool_name: Tool name.

        Returns:
            Skill name if the tool is registered, None otherwise.
        """
        info = self.get_tool_info(tool_name)
        return info.get("skill") if info else None

    def get_enabled_tools(self, enabled_names: list[str] | None = None) -> list[FunctionTool]:
        """Get enabled tools as Google ADK FunctionTool instances.

        Args:
            enabled_names: List of enabled tool names. If None, returns all tools.

        Returns:
            List of FunctionTool instances ready for use with the agent
        """
        if enabled_names is None:
            enabled_names = self.get_all_tool_names()

        tools = []
        for name in enabled_names:
            tool = self._tools.get(name)
            if tool:
                tools.append(tool.to_function_tool())

        return tools

    def get_tool_info(self, name: str) -> dict[str, Any] | None:
        """Get information about a tool.

        Args:
            name: Tool name

        Returns:
            Dictionary with tool information (name, description, skill) or None
        """
        tool = self._tools.get(name)
        if tool:
            # Find which skill this tool belongs to
            skill_name = None
            for skill in self._skills.values():
                if tool in skill.get_tools():
                    skill_name = skill.name
                    break

            return {
                "name": tool.name,
                "description": tool.description,
                "skill": skill_name,
                "requires_confirmation": tool.requires_confirmation,
            }
        return None

    def get_all_tools_info(self) -> dict[str, dict[str, Any]]:
        """Get information about all registered tools.

        Returns:
            Dictionary mapping tool names to their information
        """
        return {
            name: self.get_tool_info(name)
            for name in self._tools.keys()
            if self.get_tool_info(name)
        }

    def is_skill_registered(self, name: str) -> bool:
        """Check if a skill is registered.

        Args:
            name: Skill name

        Returns:
            True if the skill is registered, False otherwise
        """
        return name in self._skills

    def is_tool_registered(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Tool name

        Returns:
            True if the tool is registered, False otherwise
        """
        return name in self._tools


__all__ = [
    "Tool",
    "FunctionToolWrapper",
    "Skill",
    "Skill",
    "SkillRegistry",
]
