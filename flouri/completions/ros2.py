"""ROS2 command completion for Flouri."""

import subprocess

from prompt_toolkit.completion import Completion


def _get_ros2_topics() -> list[str]:
    """Get list of ROS2 topics by running ros2 topic list.

    Returns:
        List of topic names, empty list on error
    """
    try:
        result = subprocess.run(
            ["ros2", "topic", "list"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.split("\n") if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return []


def _get_ros2_services() -> list[str]:
    """Get list of ROS2 services by running ros2 service list.

    Returns:
        List of service names, empty list on error
    """
    try:
        result = subprocess.run(
            ["ros2", "service", "list"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.split("\n") if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return []


def _get_ros2_nodes() -> list[str]:
    """Get list of ROS2 nodes by running ros2 node list.

    Returns:
        List of node names, empty list on error
    """
    try:
        result = subprocess.run(
            ["ros2", "node", "list"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            # Node list format: /node_name
            return [
                line.strip().lstrip("/")
                for line in result.stdout.split("\n")
                if line.strip() and not line.strip().startswith("/")
            ]
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return []


def _get_ros2_actions() -> list[str]:
    """Get list of ROS2 actions by running ros2 action list.

    Returns:
        List of action names, empty list on error
    """
    try:
        result = subprocess.run(
            ["ros2", "action", "list"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.split("\n") if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return []


def complete_ros2(current_word: str, words: list[str], word_index: int) -> list[Completion]:
    """Complete ROS2 commands and subcommands.

    Args:
        current_word: The current word being completed
        words: All words in the command line
        word_index: Index of the current word

    Returns:
        List of Completion objects
    """
    ros2_subcommands = [
        "topic",
        "service",
        "action",
        "node",
        "param",
        "interface",
        "pkg",
        "run",
        "launch",
        "bag",
        "component",
        "daemon",
        "doctor",
        "extension_points",
        "lifecycle",
        "multicast",
        "security",
        "wtf",
    ]

    completions: list[Completion] = []

    if word_index == 1:
        # Completing ros2 subcommand
        for cmd in ros2_subcommands:
            if cmd.startswith(current_word.lower()):
                start_pos = -len(current_word) if current_word else 0
                completions.append(
                    Completion(
                        cmd,
                        start_position=start_pos,
                        display=cmd,
                    )
                )
    elif word_index == 2:
        # Completing argument to ros2 subcommand
        subcommand = words[1].lower() if len(words) > 1 else ""

        if subcommand == "topic":
            # Complete topic subcommands
            topic_subcommands = ["list", "echo", "info", "hz", "type", "pub", "bw"]
            for cmd in topic_subcommands:
                if cmd.startswith(current_word.lower()):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            cmd,
                            start_position=start_pos,
                            display=cmd,
                        )
                    )
        elif subcommand == "service":
            # Complete service subcommands
            service_subcommands = ["list", "type", "call", "find"]
            for cmd in service_subcommands:
                if cmd.startswith(current_word.lower()):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            cmd,
                            start_position=start_pos,
                            display=cmd,
                        )
                    )
        elif subcommand == "action":
            # Complete action subcommands
            action_subcommands = ["list", "info", "send_goal"]
            for cmd in action_subcommands:
                if cmd.startswith(current_word.lower()):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            cmd,
                            start_position=start_pos,
                            display=cmd,
                        )
                    )
        elif subcommand == "node":
            # Complete node subcommands
            node_subcommands = ["list", "info"]
            for cmd in node_subcommands:
                if cmd.startswith(current_word.lower()):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            cmd,
                            start_position=start_pos,
                            display=cmd,
                        )
                    )
        elif subcommand == "param":
            # Complete param subcommands
            param_subcommands = ["list", "get", "set", "describe", "delete"]
            for cmd in param_subcommands:
                if cmd.startswith(current_word.lower()):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            cmd,
                            start_position=start_pos,
                            display=cmd,
                        )
                    )
        elif subcommand == "interface":
            # Complete interface subcommands
            interface_subcommands = ["list", "show", "package"]
            for cmd in interface_subcommands:
                if cmd.startswith(current_word.lower()):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            cmd,
                            start_position=start_pos,
                            display=cmd,
                        )
                    )
        elif subcommand == "pkg":
            # Complete pkg subcommands
            pkg_subcommands = ["list", "prefix", "executables", "describe"]
            for cmd in pkg_subcommands:
                if cmd.startswith(current_word.lower()):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            cmd,
                            start_position=start_pos,
                            display=cmd,
                        )
                    )

    elif word_index == 3:
        # Completing arguments to ros2 subcommands
        subcommand = words[1].lower() if len(words) > 1 else ""
        subsubcommand = words[2].lower() if len(words) > 2 else ""

        if subcommand == "topic" and subsubcommand in ["echo", "info", "hz", "type"]:
            # Complete topic names
            topics = _get_ros2_topics()
            for topic in topics:
                if topic.startswith(current_word):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            topic,
                            start_position=start_pos,
                            display=topic,
                        )
                    )
        elif subcommand == "service" and subsubcommand in ["type", "call", "find"]:
            # Complete service names
            services = _get_ros2_services()
            for service in services:
                if service.startswith(current_word):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            service,
                            start_position=start_pos,
                            display=service,
                        )
                    )
        elif subcommand == "action" and subsubcommand in ["info", "send_goal"]:
            # Complete action names
            actions = _get_ros2_actions()
            for action in actions:
                if action.startswith(current_word):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            action,
                            start_position=start_pos,
                            display=action,
                        )
                    )
        elif subcommand == "node" and subsubcommand == "info":
            # Complete node names
            nodes = _get_ros2_nodes()
            for node in nodes:
                if node.startswith(current_word):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            node,
                            start_position=start_pos,
                            display=node,
                        )
                    )
        elif subcommand == "param" and subsubcommand in ["get", "set", "describe", "delete"]:
            # Complete node names for param commands
            nodes = _get_ros2_nodes()
            for node in nodes:
                if node.startswith(current_word):
                    start_pos = -len(current_word) if current_word else 0
                    completions.append(
                        Completion(
                            node,
                            start_position=start_pos,
                            display=node,
                        )
                    )

    return completions
