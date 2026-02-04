"""ROS2 CLI tools for interacting with ROS2 systems."""

import subprocess
from typing import Any

from google.adk.tools import ToolContext

from ...logging import log_tool_call
from .. import globals as globals_module


def _execute_ros2_command(
    subcommand: str, args: list[str] | None = None, tool_name: str = ""
) -> dict[str, Any]:
    """Execute a ROS2 command and return the result.

    Args:
        subcommand: The ROS2 subcommand (e.g., "topic", "service", "node").
        args: Additional arguments to pass to the ROS2 command.
        tool_name: Name of the tool for logging.

    Returns:
        A dictionary with status and output from the command execution.
    """
    cmd_parts = ["ros2", subcommand]
    if args:
        cmd_parts.extend(args)

    cmd = " ".join(cmd_parts)

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
            "command": cmd,
        }

        log_tool_call(
            tool_name or f"ros2_{subcommand}",
            {"command": cmd},
            result,
            success=(process.returncode == 0),
        )

        return result
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"Error executing ROS2 command: {e}",
            "command": cmd,
        }
        log_tool_call(
            tool_name or f"ros2_{subcommand}",
            {"command": cmd},
            error_result,
            success=False,
        )
        return error_result


def ros2_topic_list(tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    List all available ROS2 topics.

    Returns:
        A dictionary with status and list of topics.
    """
    return _execute_ros2_command("topic", ["list"], "ros2_topic_list")


def ros2_topic_echo(
    topic_name: str, message_type: str | None = None, tool_context: ToolContext | None = None
) -> dict[str, Any]:
    """
    Echo messages from a ROS2 topic.

    Args:
        topic_name: The name of the topic to echo.
        message_type: Optional message type to filter messages.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and output from the topic.
    """
    args = [topic_name]
    if message_type:
        args.extend(["--message-type", message_type])
    return _execute_ros2_command("topic", ["echo"] + args, "ros2_topic_echo")


def ros2_topic_info(topic_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Get information about a ROS2 topic.

    Args:
        topic_name: The name of the topic.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and topic information.
    """
    return _execute_ros2_command("topic", ["info", topic_name], "ros2_topic_info")


def ros2_topic_hz(topic_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Measure the publishing rate of a ROS2 topic.

    Args:
        topic_name: The name of the topic to measure.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and frequency information.
    """
    return _execute_ros2_command("topic", ["hz", topic_name], "ros2_topic_hz")


def ros2_topic_type(topic_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Get the message type of a ROS2 topic.

    Args:
        topic_name: The name of the topic.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and message type.
    """
    return _execute_ros2_command("topic", ["type", topic_name], "ros2_topic_type")


def ros2_service_list(tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    List all available ROS2 services.

    Returns:
        A dictionary with status and list of services.
    """
    return _execute_ros2_command("service", ["list"], "ros2_service_list")


def ros2_service_type(service_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Get the service type of a ROS2 service.

    Args:
        service_name: The name of the service.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and service type.
    """
    return _execute_ros2_command("service", ["type", service_name], "ros2_service_type")


def ros2_service_call(
    service_name: str, service_type: str, request: str, tool_context: ToolContext | None = None
) -> dict[str, Any]:
    """
    Call a ROS2 service.

    Args:
        service_name: The name of the service to call.
        service_type: The type of the service.
        request: The request message in YAML format (e.g., "{data: 'hello'}").
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and service response.
    """
    return _execute_ros2_command(
        "service", ["call", service_name, service_type, request], "ros2_service_call"
    )


def ros2_action_list(tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    List all available ROS2 actions.

    Returns:
        A dictionary with status and list of actions.
    """
    return _execute_ros2_command("action", ["list"], "ros2_action_list")


def ros2_action_info(action_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Get information about a ROS2 action.

    Args:
        action_name: The name of the action.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and action information.
    """
    return _execute_ros2_command("action", ["info", action_name], "ros2_action_info")


def ros2_node_list(tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    List all running ROS2 nodes.

    Returns:
        A dictionary with status and list of nodes.
    """
    return _execute_ros2_command("node", ["list"], "ros2_node_list")


def ros2_node_info(node_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Get information about a ROS2 node.

    Args:
        node_name: The name of the node.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and node information.
    """
    return _execute_ros2_command("node", ["info", node_name], "ros2_node_info")


def ros2_param_list(
    node_name: str | None = None, tool_context: ToolContext | None = None
) -> dict[str, Any]:
    """
    List ROS2 parameters.

    Args:
        node_name: Optional node name to list parameters for. If not provided, lists all parameters.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and list of parameters.
    """
    args = ["list"]
    if node_name:
        args.append(node_name)
    return _execute_ros2_command("param", args, "ros2_param_list")


def ros2_param_get(
    node_name: str, param_name: str, tool_context: ToolContext | None = None
) -> dict[str, Any]:
    """
    Get a ROS2 parameter value.

    Args:
        node_name: The name of the node.
        param_name: The name of the parameter.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and parameter value.
    """
    return _execute_ros2_command("param", ["get", node_name, param_name], "ros2_param_get")


def ros2_param_set(
    node_name: str, param_name: str, value: str, tool_context: ToolContext | None = None
) -> dict[str, Any]:
    """
    Set a ROS2 parameter value.

    Args:
        node_name: The name of the node.
        param_name: The name of the parameter.
        value: The value to set (as a string).
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and confirmation.
    """
    return _execute_ros2_command("param", ["set", node_name, param_name, value], "ros2_param_set")


def ros2_interface_list(tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    List all available ROS2 interfaces (messages, services, actions).

    Returns:
        A dictionary with status and list of interfaces.
    """
    return _execute_ros2_command("interface", ["list"], "ros2_interface_list")


def ros2_interface_show(
    interface_name: str, tool_context: ToolContext | None = None
) -> dict[str, Any]:
    """
    Show the definition of a ROS2 interface.

    Args:
        interface_name: The name of the interface (e.g., "std_msgs/msg/String").
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and interface definition.
    """
    return _execute_ros2_command("interface", ["show", interface_name], "ros2_interface_show")


def ros2_pkg_list(tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    List all available ROS2 packages.

    Returns:
        A dictionary with status and list of packages.
    """
    return _execute_ros2_command("pkg", ["list"], "ros2_pkg_list")


def ros2_pkg_prefix(package_name: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Get the prefix path of a ROS2 package.

    Args:
        package_name: The name of the package.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and package prefix path.
    """
    return _execute_ros2_command("pkg", ["prefix", package_name], "ros2_pkg_prefix")


# -----------------------------------------------------------------------------
# ros2 bag tools (recording, playback, info, utilities)
# -----------------------------------------------------------------------------


def ros2_bag_record(
    output_path: str,
    topics: list[str] | None = None,
    record_all: bool = False,
    storage_id: str | None = None,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """
    Record ROS2 topics to a bag file.

    Args:
        output_path: Directory path for the output bag (e.g. "my_bag" or "/path/to/my_bag").
        topics: List of topic names to record. Ignored if record_all is True.
        record_all: If True, record all topics (equivalent to -a).
        storage_id: Optional storage plugin (e.g. "sqlite3").
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and command output.
    """
    args = ["-o", output_path]
    if storage_id:
        args.extend(["--storage", storage_id])
    if record_all:
        args.append("-a")
    elif topics:
        args.extend(topics)
    return _execute_ros2_command("bag", ["record"] + args, "ros2_bag_record")


def ros2_bag_play(
    bag_path: str,
    rate: float | None = None,
    loop: bool = False,
    start_offset: float | None = None,
    delay: float | None = None,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """
    Play back a ROS2 bag file.

    Args:
        bag_path: Path to the bag directory or bag file.
        rate: Playback rate multiplier (e.g. 1.0 = realtime, 2.0 = double speed).
        loop: If True, loop playback.
        start_offset: Start playback at this offset in seconds.
        delay: Delay before starting playback in seconds.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and command output.
    """
    args = [bag_path]
    if rate is not None:
        args.extend(["--rate", str(rate)])
    if loop:
        args.append("--loop")
    if start_offset is not None:
        args.extend(["--start-offset", str(start_offset)])
    if delay is not None:
        args.extend(["--delay", str(delay)])
    return _execute_ros2_command("bag", ["play"] + args, "ros2_bag_play")


def ros2_bag_info(bag_path: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Show metadata and summary for a ROS2 bag file.

    Args:
        bag_path: Path to the bag directory or bag file.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and bag info (duration, topics, message counts, etc.).
    """
    return _execute_ros2_command("bag", ["info", bag_path], "ros2_bag_info")


def ros2_bag_reindex(bag_path: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Reindex a ROS2 bag (e.g. after corruption or incomplete write).

    Args:
        bag_path: Path to the bag directory.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and command output.
    """
    return _execute_ros2_command("bag", ["reindex", bag_path], "ros2_bag_reindex")


def ros2_bag_compress(
    bag_path: str,
    output_path: str | None = None,
    compression_mode: str | None = None,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """
    Compress a ROS2 bag file (when supported by the distro).

    Args:
        bag_path: Path to the bag directory.
        output_path: Optional output path for compressed bag.
        compression_mode: Optional compression mode (e.g. "FILE", "MESSAGE").
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and command output.
    """
    args = [bag_path]
    if output_path:
        args.extend(["-o", output_path])
    if compression_mode:
        args.extend(["--compression-mode", compression_mode])
    return _execute_ros2_command("bag", ["compress"] + args, "ros2_bag_compress")


def ros2_bag_decompress(
    bag_path: str,
    output_path: str | None = None,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """
    Decompress a ROS2 bag file (when supported by the distro).

    Args:
        bag_path: Path to the compressed bag directory.
        output_path: Optional output path for decompressed bag.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and command output.
    """
    args = [bag_path]
    if output_path:
        args.extend(["-o", output_path])
    return _execute_ros2_command("bag", ["decompress"] + args, "ros2_bag_decompress")


def ros2_bag_validate(bag_path: str, tool_context: ToolContext | None = None) -> dict[str, Any]:
    """
    Validate a ROS2 bag file (integrity and metadata).

    Args:
        bag_path: Path to the bag directory.
        tool_context: Tool context (ignored, kept for compatibility).

    Returns:
        A dictionary with status and validation result.
    """
    return _execute_ros2_command("bag", ["validate", bag_path], "ros2_bag_validate")
