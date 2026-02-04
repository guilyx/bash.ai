"""Configuration management skill."""

from ..base import BaseSkill, FunctionToolWrapper
from .config_tools import (
    add_to_allowlist,
    add_to_blacklist,
    is_in_allowlist,
    is_in_blacklist,
    list_allowlist,
    list_blacklist,
    remove_from_allowlist,
    remove_from_blacklist,
)


class ConfigSkill(BaseSkill):
    """Configuration management skill."""

    def __init__(self):
        """Initialize the config skill."""
        super().__init__(
            name="config",
            description="Configuration and allowlist/blacklist management",
            tools=[
                FunctionToolWrapper(
                    "add_to_allowlist",
                    add_to_allowlist,
                    "Add a command to the allowlist",
                    requires_confirmation=False,
                ),
                FunctionToolWrapper(
                    "remove_from_allowlist",
                    remove_from_allowlist,
                    "Remove a command from the allowlist",
                    requires_confirmation=False,
                ),
                FunctionToolWrapper(
                    "add_to_blacklist",
                    add_to_blacklist,
                    "Add a command to the blacklist",
                    requires_confirmation=False,
                ),
                FunctionToolWrapper(
                    "remove_from_blacklist",
                    remove_from_blacklist,
                    "Remove a command from the blacklist",
                    requires_confirmation=False,
                ),
                FunctionToolWrapper(
                    "list_allowlist",
                    list_allowlist,
                    "List all commands in the allowlist",
                ),
                FunctionToolWrapper(
                    "list_blacklist",
                    list_blacklist,
                    "List all commands in the blacklist",
                ),
                FunctionToolWrapper(
                    "is_in_allowlist",
                    is_in_allowlist,
                    "Check if a command is in the allowlist",
                ),
                FunctionToolWrapper(
                    "is_in_blacklist",
                    is_in_blacklist,
                    "Check if a command is in the blacklist",
                ),
            ],
        )
