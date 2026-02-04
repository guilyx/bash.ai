"""Tests for the skill system."""

import pytest

from flourish.tools import (
    BaseSkill,
    FunctionToolWrapper,
    Skill,
    SkillRegistry,
    Tool,
    get_registry,
)
from flourish.tools.bash.skill import BashSkill
from flourish.tools.config.skill import ConfigSkill
from flourish.tools.history.skill import HistorySkill
from flourish.tools.ros2.skill import ROS2Skill
from flourish.tools.system.skill import SystemSkill
from flourish.tools.tool_manager.skill import ToolManagerSkill


def test_tool_base_class():
    """Test that Tool is an abstract base class."""

    class TestTool(Tool):
        @property
        def name(self) -> str:
            return "test_tool"

        @property
        def description(self) -> str:
            return "Test tool description"

        def get_function(self):
            def test_func():
                return {"status": "success"}

            return test_func

    tool = TestTool()
    assert tool.name == "test_tool"
    assert tool.description == "Test tool description"
    assert callable(tool.get_function())
    assert not tool.requires_confirmation


def test_function_tool_wrapper():
    """Test FunctionToolWrapper."""

    def test_func():
        return {"status": "success"}

    wrapper = FunctionToolWrapper(
        "test_tool", test_func, "Test tool description", requires_confirmation=True
    )
    assert wrapper.name == "test_tool"
    assert wrapper.description == "Test tool description"
    assert wrapper.requires_confirmation is True
    assert wrapper.get_function() == test_func


def test_skill_base_class():
    """Test that Skill is an abstract base class."""

    class TestSkill(Skill):
        @property
        def name(self) -> str:
            return "test_skill"

        @property
        def description(self) -> str:
            return "Test skill description"

        def get_tools(self) -> list[Tool]:
            return []

    skill = TestSkill()
    assert skill.name == "test_skill"
    assert skill.description == "Test skill description"
    assert skill.get_tools() == []
    assert skill.get_tool("nonexistent") is None


def test_base_skill():
    """Test BaseSkill implementation."""

    def tool1_func():
        return {"status": "success"}

    def tool2_func():
        return {"status": "success"}

    tools = [
        FunctionToolWrapper("tool1", tool1_func, "Tool 1 description"),
        FunctionToolWrapper("tool2", tool2_func, "Tool 2 description"),
    ]

    skill = BaseSkill(
        name="test_skill",
        description="Test skill description",
        tools=tools,
    )

    assert skill.name == "test_skill"
    assert skill.description == "Test skill description"
    assert len(skill.get_tools()) == 2
    assert skill.get_tool("tool1") is not None
    assert skill.get_tool("tool1").name == "tool1"
    assert skill.get_tool("nonexistent") is None


def test_skill_registry():
    """Test SkillRegistry functionality."""
    registry = SkillRegistry()

    def tool_func():
        return {"status": "success"}

    tool = FunctionToolWrapper("test_tool", tool_func, "Test tool")
    skill = BaseSkill("test_skill", "Test skill", [tool])

    # Register skill
    registry.register(skill)

    # Test getting skill
    assert registry.get_skill("test_skill") == skill
    assert registry.get_skill("nonexistent") is None

    # Test getting tool
    assert registry.get_tool("test_tool") == tool
    assert registry.get_tool("nonexistent") is None

    # Test getting all skills
    all_skills = registry.get_all_skills()
    assert "test_skill" in all_skills
    assert len(all_skills) == 1

    # Test getting all tools
    all_tools = registry.get_all_tools()
    assert "test_tool" in all_tools
    assert len(all_tools) == 1

    # Test getting tools by skill
    tools_by_skill = registry.get_tools_by_skill("test_skill")
    assert "test_tool" in tools_by_skill
    assert len(tools_by_skill) == 1

    # Test duplicate registration
    duplicate_skill = BaseSkill("test_skill", "Duplicate", [])
    with pytest.raises(ValueError, match="already registered"):
        registry.register(duplicate_skill)

    # Test duplicate tool registration
    duplicate_tool = FunctionToolWrapper("test_tool", tool_func, "Duplicate tool")
    duplicate_skill2 = BaseSkill("test_skill2", "Test", [duplicate_tool])
    with pytest.raises(ValueError, match="already registered"):
        registry.register(duplicate_skill2)


def test_get_registry():
    """Test get_registry function."""
    registry1 = get_registry()
    registry2 = get_registry()

    # Should return the same instance
    assert registry1 is registry2

    # Should have all skills registered
    skill_names = registry1.get_all_skill_names()
    assert "bash" in skill_names
    assert "config" in skill_names
    assert "history" in skill_names
    assert "system" in skill_names
    assert "ros2" in skill_names
    assert "tool_manager" in skill_names


def test_bash_skill():
    """Test BashSkill."""
    skill = BashSkill()
    assert skill.name == "bash"
    assert "bash" in skill.description.lower()
    tools = skill.get_tools()
    assert len(tools) == 3
    tool_names = [tool.name for tool in tools]
    assert "execute_bash" in tool_names
    assert "get_user" in tool_names
    assert "set_cwd" in tool_names


def test_config_skill():
    """Test ConfigSkill."""
    skill = ConfigSkill()
    assert skill.name == "config"
    assert "config" in skill.description.lower()
    tools = skill.get_tools()
    assert len(tools) == 8
    tool_names = [tool.name for tool in tools]
    assert "add_to_allowlist" in tool_names
    assert "remove_from_allowlist" in tool_names
    assert "add_to_blacklist" in tool_names
    assert "remove_from_blacklist" in tool_names
    assert "list_allowlist" in tool_names
    assert "list_blacklist" in tool_names
    assert "is_in_allowlist" in tool_names
    assert "is_in_blacklist" in tool_names


def test_history_skill():
    """Test HistorySkill."""
    skill = HistorySkill()
    assert skill.name == "history"
    assert "history" in skill.description.lower()
    tools = skill.get_tools()
    assert len(tools) == 2
    tool_names = [tool.name for tool in tools]
    assert "read_bash_history" in tool_names
    assert "read_conversation_history" in tool_names


def test_system_skill():
    """Test SystemSkill."""
    skill = SystemSkill()
    assert skill.name == "system"
    assert "system" in skill.description.lower()
    tools = skill.get_tools()
    assert len(tools) == 1
    assert tools[0].name == "get_current_datetime"


def test_ros2_skill():
    """Test ROS2Skill."""
    skill = ROS2Skill()
    assert skill.name == "ros2"
    assert "ros2" in skill.description.lower()
    tools = skill.get_tools()
    assert len(tools) == 26  # topics, services, actions, nodes, params, interfaces, pkgs, bag tools
    tool_names = [tool.name for tool in tools]
    assert "ros2_topic_list" in tool_names
    assert "ros2_service_list" in tool_names
    assert "ros2_node_list" in tool_names


def test_tool_manager_skill():
    """Test ToolManagerSkill."""
    skill = ToolManagerSkill()
    assert skill.name == "tool_manager"
    assert "tool" in skill.description.lower()
    tools = skill.get_tools()
    assert len(tools) == 4
    tool_names = [tool.name for tool in tools]
    assert "get_available_tools" in tool_names
    assert "list_enabled_tools" in tool_names
    assert "enable_tool" in tool_names
    assert "disable_tool" in tool_names


def test_registry_tool_info():
    """Test getting tool information from registry."""
    registry = get_registry()

    # Test getting info for a specific tool
    tool_info = registry.get_tool_info("execute_bash")
    assert tool_info is not None
    assert tool_info["name"] == "execute_bash"
    assert "description" in tool_info
    assert "skill" in tool_info
    assert tool_info["skill"] == "bash"
    assert "requires_confirmation" in tool_info

    # Test getting info for nonexistent tool
    assert registry.get_tool_info("nonexistent_tool") is None

    # Test getting all tools info
    all_info = registry.get_all_tools_info()
    assert len(all_info) > 0
    assert "execute_bash" in all_info
    assert all_info["execute_bash"]["skill"] == "bash"


def test_registry_enabled_tools():
    """Test getting enabled tools from registry."""
    registry = get_registry()

    # Get all tools
    all_tools = registry.get_enabled_tools()
    assert len(all_tools) > 0

    # Get specific tools
    enabled_names = ["execute_bash", "get_user"]
    specific_tools = registry.get_enabled_tools(enabled_names)
    assert len(specific_tools) == 2

    # Get nonexistent tool (should be filtered out)
    nonexistent_tools = registry.get_enabled_tools(["nonexistent_tool"])
    assert len(nonexistent_tools) == 0


def test_registry_get_tool_names_for_skills():
    """Test getting tool names from a set of skills."""
    registry = get_registry()

    names = registry.get_tool_names_for_skills(["bash"])
    assert "execute_bash" in names
    assert "get_user" in names
    assert "set_cwd" in names

    names_multi = registry.get_tool_names_for_skills(["bash", "system"])
    assert "execute_bash" in names_multi
    assert "get_current_datetime" in names_multi
    assert names_multi == sorted(names_multi)

    assert registry.get_tool_names_for_skills(["nonexistent"]) == []
    assert registry.get_tool_names_for_skills([]) == []


def test_registry_get_skill_for_tool():
    """Test resolving tool name to skill name."""
    registry = get_registry()

    assert registry.get_skill_for_tool("execute_bash") == "bash"
    assert registry.get_skill_for_tool("ros2_topic_list") == "ros2"
    assert registry.get_skill_for_tool("list_enabled_tools") == "tool_manager"
    assert registry.get_skill_for_tool("nonexistent_tool") is None


def test_registry_checks():
    """Test registry check methods."""
    registry = get_registry()

    # Test skill checks
    assert registry.is_skill_registered("bash") is True
    assert registry.is_skill_registered("nonexistent") is False

    # Test tool checks
    assert registry.is_tool_registered("execute_bash") is True
    assert registry.is_tool_registered("nonexistent") is False


def test_tool_to_function_tool():
    """Test converting Tool to FunctionTool."""
    registry = get_registry()
    tool = registry.get_tool("execute_bash")
    assert tool is not None

    function_tool = tool.to_function_tool()
    assert function_tool is not None
    assert hasattr(function_tool, "func") or callable(function_tool)


def test_skill_get_tool():
    """Test Skill.get_tool method."""
    skill = BashSkill()
    tool = skill.get_tool("execute_bash")
    assert tool is not None
    assert tool.name == "execute_bash"

    assert skill.get_tool("nonexistent") is None
