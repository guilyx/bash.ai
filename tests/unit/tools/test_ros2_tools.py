"""Unit tests for ROS2 tools (mocked subprocess)."""

from unittest.mock import MagicMock, patch

import pytest

from flourish.tools.ros2 import ros2_tools


@pytest.fixture(autouse=True)
def mock_log_tool_call():
    with patch("flourish.tools.ros2.ros2_tools.log_tool_call"):
        yield


def test_execute_ros2_command_success():
    """_execute_ros2_command returns success when process returncode is 0."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = ("topic1\ntopic2", "")

    with patch("flourish.tools.ros2.ros2_tools.subprocess.Popen", return_value=mock_process):
        result = ros2_tools._execute_ros2_command("topic", ["list"], "ros2_topic_list")

    assert result["status"] == "success"
    assert result["stdout"] == "topic1\ntopic2"
    assert result["exit_code"] == 0
    assert "ros2 topic list" in result["command"]


def test_execute_ros2_command_nonzero_exit():
    """_execute_ros2_command returns error status when process returncode != 0."""
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = ("", "ros2 not found")

    with patch("flourish.tools.ros2.ros2_tools.subprocess.Popen", return_value=mock_process):
        result = ros2_tools._execute_ros2_command("topic", ["list"], "ros2_topic_list")

    assert result["status"] == "error"
    assert result["exit_code"] == 1
    assert "ros2 not found" in result["stderr"]


def test_execute_ros2_command_exception():
    """_execute_ros2_command returns error dict when Popen raises."""
    with patch("flourish.tools.ros2.ros2_tools.subprocess.Popen", side_effect=FileNotFoundError("ros2 not found")):
        result = ros2_tools._execute_ros2_command("topic", ["list"], "ros2_topic_list")

    assert result["status"] == "error"
    assert "message" in result
    assert "ros2" in result["message"].lower() or "error" in result["message"].lower()


def test_execute_ros2_command_streaming_success():
    """_execute_ros2_command_streaming returns when process exits."""
    mock_process = MagicMock()
    mock_process.returncode = 0

    with patch("flourish.tools.ros2.ros2_tools.subprocess.Popen", return_value=mock_process):
        result = ros2_tools._execute_ros2_command_streaming("bag", ["record", "-a"], "ros2_bag_record")

    assert result["status"] == "success"
    assert result["exit_code"] == 0
    mock_process.wait.assert_called_once()


def test_execute_ros2_command_streaming_exception():
    """_execute_ros2_command_streaming returns error when Popen raises."""
    with patch("flourish.tools.ros2.ros2_tools.subprocess.Popen", side_effect=OSError("resource unavailable")):
        result = ros2_tools._execute_ros2_command_streaming("bag", ["record"], "ros2_bag_record")

    assert result["status"] == "error"
    assert "message" in result


def test_ros2_topic_list():
    """ros2_topic_list calls _execute_ros2_command with topic list."""
    with patch.object(ros2_tools, "_execute_ros2_command") as mock_exec:
        mock_exec.return_value = {"status": "success", "stdout": "/topic1\n/topic2"}
        result = ros2_tools.ros2_topic_list()

    mock_exec.assert_called_once_with("topic", ["list"], "ros2_topic_list")
    assert result["status"] == "success"


def test_ros2_node_list():
    """ros2_node_list calls _execute_ros2_command with node list."""
    with patch.object(ros2_tools, "_execute_ros2_command") as mock_exec:
        mock_exec.return_value = {"status": "success", "stdout": "/node1"}
        result = ros2_tools.ros2_node_list()

    mock_exec.assert_called_once_with("node", ["list"], "ros2_node_list")
    assert result["status"] == "success"


def test_ros2_topic_echo():
    """ros2_topic_echo passes topic name as argument."""
    with patch.object(ros2_tools, "_execute_ros2_command") as mock_exec:
        mock_exec.return_value = {"status": "success"}
        result = ros2_tools.ros2_topic_echo("/cmd_vel")

    mock_exec.assert_called_once_with("topic", ["echo", "/cmd_vel"], "ros2_topic_echo")
    assert result["status"] == "success"


def test_ros2_service_list():
    """ros2_service_list calls _execute_ros2_command."""
    with patch.object(ros2_tools, "_execute_ros2_command") as mock_exec:
        mock_exec.return_value = {"status": "success"}
        result = ros2_tools.ros2_service_list()

    mock_exec.assert_called_once_with("service", ["list"], "ros2_service_list")


def test_ros2_param_list():
    """ros2_param_list calls _execute_ros2_command with node name when provided."""
    with patch.object(ros2_tools, "_execute_ros2_command") as mock_exec:
        mock_exec.return_value = {"status": "success"}
        result = ros2_tools.ros2_param_list(node_name="/my_node")

    mock_exec.assert_called_once_with("param", ["list", "/my_node"], "ros2_param_list")


def test_ros2_topic_info():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_topic_info("/cmd_vel")
    assert result["status"] == "success"


def test_ros2_topic_hz():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_topic_hz("/scan")
    assert result["status"] == "success"


def test_ros2_topic_type():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_topic_type("/odom")
    assert result["status"] == "success"


def test_ros2_service_type():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_service_type("/my_service")
    assert result["status"] == "success"


def test_ros2_service_call():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_service_call("srv", "std_srvs/srv/Empty", "{}")
    assert result["status"] == "success"


def test_ros2_action_list():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_action_list()
    assert result["status"] == "success"


def test_ros2_action_info():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_action_info("/navigate")
    assert result["status"] == "success"


def test_ros2_node_info():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_node_info("/listener")
    assert result["status"] == "success"


def test_ros2_param_get():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_param_get("/node", "param_name")
    assert result["status"] == "success"


def test_ros2_param_set():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_param_set("/node", "param", "value")
    assert result["status"] == "success"


def test_ros2_interface_list():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_interface_list()
    assert result["status"] == "success"


def test_ros2_interface_show():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_interface_show("std_msgs/msg/String")
    assert result["status"] == "success"


def test_ros2_pkg_list():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_pkg_list()
    assert result["status"] == "success"


def test_ros2_pkg_prefix():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_pkg_prefix("my_pkg")
    assert result["status"] == "success"


def test_ros2_bag_info():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_bag_info("/path/to/bag")
    assert result["status"] == "success"


def test_ros2_bag_reindex():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_bag_reindex("/path/to/bag")
    assert result["status"] == "success"


def test_ros2_bag_validate():
    with patch.object(ros2_tools, "_execute_ros2_command", return_value={"status": "success"}):
        result = ros2_tools.ros2_bag_validate("/path/to/bag")
    assert result["status"] == "success"
