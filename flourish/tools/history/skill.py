"""History management skill."""

from ..base import BaseSkill, FunctionToolWrapper
from .history_tools import (
    get_tool_call_stats,
    read_bash_history,
    read_conversation_history,
)


class HistorySkill(BaseSkill):
    """History management skill."""

    def __init__(self):
        """Initialize the history skill."""
        super().__init__(
            name="history",
            description="History-related tools for reading command and conversation history",
            tools=[
                FunctionToolWrapper(
                    "read_bash_history",
                    read_bash_history,
                    "Read bash command history",
                ),
                FunctionToolWrapper(
                    "read_conversation_history",
                    read_conversation_history,
                    "Read conversation history",
                ),
                FunctionToolWrapper(
                    "get_tool_call_stats",
                    get_tool_call_stats,
                    "Parse tool-call history from session logs and return stats (counts, success rate, duration)",
                ),
            ],
        )
