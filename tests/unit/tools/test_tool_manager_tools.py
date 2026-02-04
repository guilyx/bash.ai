"""Unit tests for tool_manager tools."""

from unittest.mock import patch

import pytest

from flourish.tools.tool_manager import tool_manager_tools


@pytest.fixture(autouse=True)
def mock_log_tool_call():
    """Avoid creating real session log files when tools call log_tool_call."""
    with patch("flourish.tools.tool_manager.tool_manager_tools.log_tool_call"):
        yield


def test_list_enabled_tools_success():
    """list_enabled_tools returns derived tool names when config and registry work."""
    with patch.object(tool_manager_tools, "_get_enabled_tool_names") as mock_get:
        mock_get.return_value = ["execute_bash", "get_user", "set_cwd"]
        result = tool_manager_tools.list_enabled_tools()

    assert result["status"] == "success"
    assert result["enabled_tools"] == ["execute_bash", "get_user", "set_cwd"]
    assert result["count"] == 3


def test_list_enabled_tools_error():
    """list_enabled_tools returns error when _get_enabled_tool_names raises."""
    with patch.object(tool_manager_tools, "_get_enabled_tool_names") as mock_get:
        mock_get.side_effect = RuntimeError("config error")
        result = tool_manager_tools.list_enabled_tools()

    assert result["status"] == "error"
    assert "message" in result


def test_get_available_tools_success():
    """get_available_tools returns registry tool info when registry works."""
    with patch("flourish.tools.registry.get_registry") as mock_reg:
        mock_reg.return_value.get_all_tools_info.return_value = {
            "execute_bash": {"description": "Run bash command"},
            "get_user": {"description": "Get current user"},
        }
        result = tool_manager_tools.get_available_tools()

    assert result["status"] == "success"
    assert result["count"] == 2
    assert "execute_bash" in result["available_tools"]
    assert result["available_tools"]["execute_bash"] == "Run bash command"


def test_get_available_tools_error():
    """get_available_tools returns error when registry raises."""
    with patch("flourish.tools.registry.get_registry") as mock_reg:
        mock_reg.side_effect = ImportError("no registry")
        result = tool_manager_tools.get_available_tools()

    assert result["status"] == "error"
    assert result["available_tools"] == {}
    assert result["count"] == 0


def test_enable_tool_unknown_tool():
    """enable_tool returns error for unknown tool name."""
    with patch("flourish.tools.registry.get_registry") as mock_reg:
        mock_reg.return_value.get_skill_for_tool.return_value = None
        result = tool_manager_tools.enable_tool("nonexistent_tool")

    assert result["status"] == "error"
    assert "Unknown tool" in result["message"]


def test_enable_tool_success():
    """enable_tool adds skill and returns updated list."""
    with patch("flourish.tools.registry.get_registry") as mock_reg:
        with patch("flourish.tools.tool_manager.tool_manager_tools.ConfigManager") as mock_cm:
            with patch.object(tool_manager_tools, "_get_enabled_tool_names") as mock_get:
                mock_reg.return_value.get_skill_for_tool.return_value = "ros2"
                mock_get.return_value = ["execute_bash", "ros2_topic_list"]
                result = tool_manager_tools.enable_tool("ros2_topic_list")

    assert result["status"] == "success"
    assert "ros2" in result["message"]
    mock_cm.return_value.add_skill.assert_called_once_with("ros2")


def test_disable_tool_unknown_tool():
    """disable_tool returns error for unknown tool name."""
    with patch("flourish.tools.registry.get_registry") as mock_reg:
        mock_reg.return_value.get_skill_for_tool.return_value = None
        result = tool_manager_tools.disable_tool("nonexistent_tool")

    assert result["status"] == "error"


def test_disable_tool_success():
    """disable_tool removes skill and returns updated list."""
    with patch("flourish.tools.registry.get_registry") as mock_reg:
        with patch("flourish.tools.tool_manager.tool_manager_tools.ConfigManager") as mock_cm:
            with patch.object(tool_manager_tools, "_get_enabled_tool_names") as mock_get:
                mock_reg.return_value.get_skill_for_tool.return_value = "ros2"
                mock_get.return_value = ["execute_bash"]
                result = tool_manager_tools.disable_tool("ros2_topic_list")

    assert result["status"] == "success"
    mock_cm.return_value.remove_skill.assert_called_once_with("ros2")


def test_enable_tool_invokes_get_enabled_tool_names():
    """enable_tool calls _get_enabled_tool_names (covers its body)."""
    with patch("flourish.tools.registry.get_registry") as mock_get_reg:
        with patch("flourish.tools.tool_manager.tool_manager_tools.ConfigManager") as mock_cm:
            mock_reg = mock_get_reg.return_value
            mock_reg.get_skill_for_tool.return_value = "ros2"
            mock_reg.get_tool_names_for_skills.return_value = ["execute_bash", "ros2_topic_list"]
            mock_cm.return_value.get_enabled_skills.return_value = ["bash", "ros2"]
            result = tool_manager_tools.enable_tool("ros2_topic_list")
    assert result["status"] == "success"
    assert result["enabled_tools"] == ["execute_bash", "ros2_topic_list"]


def test_enable_tool_exception_path():
    """enable_tool returns error and logs when add_skill raises."""
    with patch("flourish.tools.registry.get_registry") as mock_reg:
        with patch("flourish.tools.tool_manager.tool_manager_tools.ConfigManager") as mock_cm:
            with patch.object(tool_manager_tools, "_get_enabled_tool_names") as mock_get:
                mock_reg.return_value.get_skill_for_tool.return_value = "ros2"
                mock_cm.return_value.add_skill.side_effect = OSError("write failed")
                mock_get.return_value = []
                result = tool_manager_tools.enable_tool("ros2_topic_list")

    assert result["status"] == "error"
    assert "Failed to enable tool" in result["message"]


def test_disable_tool_exception_path():
    """disable_tool returns error and logs when remove_skill raises."""
    with patch("flourish.tools.registry.get_registry") as mock_reg:
        with patch("flourish.tools.tool_manager.tool_manager_tools.ConfigManager") as mock_cm:
            with patch.object(tool_manager_tools, "_get_enabled_tool_names"):
                mock_reg.return_value.get_skill_for_tool.return_value = "ros2"
                mock_cm.return_value.remove_skill.side_effect = PermissionError("read-only config")
                result = tool_manager_tools.disable_tool("ros2_topic_list")

    assert result["status"] == "error"
    assert "Failed to disable tool" in result["message"]
