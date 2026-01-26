"""Agent definitions for bash.ai."""

import os

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from google.adk.planners import BuiltInPlanner

from ..config import get_settings
from ..tools import get_bash_tools


def build_agent_instruction() -> str:
    """Build the instruction for the agent.

    Returns:
        Instruction string for the agent
    """
    instruction = """You are an AI-powered bash environment assistant that helps developers with terminal operations and workflows.

## Your Role

Execute terminal commands to accomplish tasks. Provide chain of thoughts explaining your reasoning and actions. Never ask for confirmation - the system handles security automatically.

## How You Work

1. Use `execute_bash` to run commands. If it returns "pending_confirmation", call `add_to_allowlist` with the base command, then retry.
2. Use `set_cwd` to change directories when needed.
3. Use `is_in_allowlist` and `is_in_blacklist` to check command permissions before execution.
4. Automatically add safe commands to allowlist when they require confirmation.
5. Automatically add dangerous commands to blacklist when encountered.

## Security

Never ask for confirmation. The system handles security checks automatically. Execute commands directly when appropriate.
"""

    return instruction


def get_agent(
    allowed_commands: list[str] | None = None,
    blacklisted_commands: list[str] | None = None,
) -> LlmAgent:
    """Create and return the agent with code execution capabilities.

    Args:
        allowed_commands: Optional list of allowed commands (overrides default)
        blacklisted_commands: Optional list of blacklisted commands (overrides default)

    Returns:
        LlmAgent: The configured agent with code execution
    """
    settings = get_settings()

    # Suppress Gemini via LiteLLM warning
    os.environ.setdefault("ADK_SUPPRESS_GEMINI_LITELLM_WARNINGS", "true")

    # Set API key for LiteLLM
    if settings.api_key:
        os.environ.setdefault("OPENAI_API_KEY", settings.api_key)
        # Also set provider-specific keys if needed
        if settings.model.startswith("anthropic/"):
            os.environ.setdefault("ANTHROPIC_API_KEY", settings.api_key)
        elif settings.model.startswith("gemini/") or "gemini" in settings.model.lower():
            os.environ.setdefault("GOOGLE_API_KEY", settings.api_key)

    # Use provided lists or defaults
    allowed = allowed_commands if allowed_commands is not None else settings.default_allowlist
    blacklisted = (
        blacklisted_commands if blacklisted_commands is not None else settings.default_blacklist
    )

    instruction = build_agent_instruction()

    # Get bash execution tools with allowlist/blacklist
    bash_tools = get_bash_tools(allowlist=allowed, blacklist=blacklisted)

    # Create LiteLLM model wrapper
    lite_llm_model = LiteLlm(model=settings.model)

    # Create agent with LiteLLM model and custom bash tools
    agent = LlmAgent(
        name="bash_agent",
        model=lite_llm_model,
        tools=bash_tools,
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,  # capture intermediate reasoning
                thinking_budget=15000,  # tokens allocated for planning
            )
        ),
        description="An AI-powered bash environment assistant that can answer questions and execute terminal commands to help with complex workflows.",
        instruction=instruction,
    )

    return agent
