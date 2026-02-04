"""ROS2 CLI skill."""

from ..base import BaseSkill, FunctionToolWrapper
from .ros2_tools import (
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


class ROS2Skill(BaseSkill):
    """ROS2 CLI skill."""

    def __init__(self):
        """Initialize the ROS2 skill."""
        super().__init__(
            name="ros2",
            description="ROS2 CLI tools for interacting with ROS2 systems",
            tools=[
                FunctionToolWrapper("ros2_topic_list", ros2_topic_list, "List ROS2 topics"),
                FunctionToolWrapper(
                    "ros2_topic_echo", ros2_topic_echo, "Echo messages from a ROS2 topic"
                ),
                FunctionToolWrapper(
                    "ros2_topic_info", ros2_topic_info, "Get information about a ROS2 topic"
                ),
                FunctionToolWrapper(
                    "ros2_topic_hz", ros2_topic_hz, "Measure the publishing rate of a ROS2 topic"
                ),
                FunctionToolWrapper(
                    "ros2_topic_type", ros2_topic_type, "Get the message type of a ROS2 topic"
                ),
                FunctionToolWrapper("ros2_service_list", ros2_service_list, "List ROS2 services"),
                FunctionToolWrapper("ros2_service_type", ros2_service_type, "Get the service type"),
                FunctionToolWrapper("ros2_service_call", ros2_service_call, "Call a ROS2 service"),
                FunctionToolWrapper("ros2_action_list", ros2_action_list, "List ROS2 actions"),
                FunctionToolWrapper(
                    "ros2_action_info", ros2_action_info, "Get information about a ROS2 action"
                ),
                FunctionToolWrapper("ros2_node_list", ros2_node_list, "List ROS2 nodes"),
                FunctionToolWrapper(
                    "ros2_node_info", ros2_node_info, "Get information about a ROS2 node"
                ),
                FunctionToolWrapper("ros2_param_list", ros2_param_list, "List ROS2 parameters"),
                FunctionToolWrapper("ros2_param_get", ros2_param_get, "Get a ROS2 parameter value"),
                FunctionToolWrapper("ros2_param_set", ros2_param_set, "Set a ROS2 parameter value"),
                FunctionToolWrapper(
                    "ros2_interface_list", ros2_interface_list, "List ROS2 interfaces"
                ),
                FunctionToolWrapper(
                    "ros2_interface_show", ros2_interface_show, "Show ROS2 interface definition"
                ),
                FunctionToolWrapper("ros2_pkg_list", ros2_pkg_list, "List ROS2 packages"),
                FunctionToolWrapper(
                    "ros2_pkg_prefix", ros2_pkg_prefix, "Get the prefix path of a ROS2 package"
                ),
                # Bag tools: record, play, info, utilities
                FunctionToolWrapper(
                    "ros2_bag_record",
                    ros2_bag_record,
                    "Record ROS2 topics to a bag file (output path, optional topics or record all)",
                ),
                FunctionToolWrapper(
                    "ros2_bag_play",
                    ros2_bag_play,
                    "Play back a ROS2 bag (path, optional rate, loop, delay)",
                ),
                FunctionToolWrapper(
                    "ros2_bag_info",
                    ros2_bag_info,
                    "Show metadata and summary for a ROS2 bag file",
                ),
                FunctionToolWrapper(
                    "ros2_bag_reindex",
                    ros2_bag_reindex,
                    "Reindex a ROS2 bag (e.g. after corruption or incomplete write)",
                ),
                FunctionToolWrapper(
                    "ros2_bag_compress",
                    ros2_bag_compress,
                    "Compress a ROS2 bag file (when supported by distro)",
                ),
                FunctionToolWrapper(
                    "ros2_bag_decompress",
                    ros2_bag_decompress,
                    "Decompress a ROS2 bag file (when supported by distro)",
                ),
                FunctionToolWrapper(
                    "ros2_bag_validate",
                    ros2_bag_validate,
                    "Validate a ROS2 bag file (integrity and metadata)",
                ),
            ],
        )
