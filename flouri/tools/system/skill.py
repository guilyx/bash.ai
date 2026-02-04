"""System information skill."""

from ..base import BaseSkill
from .system_tools import GetCurrentDatetimeTool


class SystemSkill(BaseSkill):
    """Skill providing system information tools."""

    def __init__(self):
        """Initialize the system skill."""
        super().__init__(
            name="system",
            description="System information and utilities",
            tools=[GetCurrentDatetimeTool()],
        )
