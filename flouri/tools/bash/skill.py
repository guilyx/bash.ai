"""Bash execution skill."""

from ..base import BaseSkill, FunctionToolWrapper
from .bash_tools import execute_bash, get_user, set_cwd


class BashSkill(BaseSkill):
    """Bash execution skill."""

    def __init__(self):
        """Initialize the bash skill."""
        super().__init__(
            name="bash",
            description="Bash command execution and directory management",
            tools=[
                FunctionToolWrapper(
                    "execute_bash",
                    execute_bash,
                    "Execute bash commands in the terminal",
                    requires_confirmation=False,
                ),
                FunctionToolWrapper(
                    "get_user",
                    get_user,
                    "Get current user information",
                ),
                FunctionToolWrapper(
                    "set_cwd",
                    set_cwd,
                    "Set the working directory",
                ),
            ],
        )
