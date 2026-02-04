"""Unit tests for agent module."""

from unittest.mock import MagicMock, patch

import pytest

from flourish.agent import agents


def test_build_agent_instruction():
    """build_agent_instruction returns non-empty string with expected content."""
    instruction = agents.build_agent_instruction()
    assert isinstance(instruction, str)
    assert len(instruction) > 0
    assert "execute_bash" in instruction
    assert "allowlist" in instruction.lower() or "allowlist" in instruction
    assert "set_cwd" in instruction
    assert "blacklist" in instruction.lower() or "blacklist" in instruction


def test_get_agent_returns_llm_agent():
    """get_agent returns an LlmAgent when settings and tools are available."""
    mock_settings = MagicMock()
    mock_settings.api_key = "test-key"
    mock_settings.model = "gpt-4o-mini"
    mock_settings.default_allowlist = ["ls", "pwd"]
    mock_settings.default_blacklist = ["rm"]

    with patch("flourish.agent.agents.get_settings", return_value=mock_settings):
        with patch("flourish.agent.agents.get_bash_tools") as mock_bash_tools:
            mock_bash_tools.return_value = []
            agent = agents.get_agent()

    from google.adk.agents import LlmAgent

    assert isinstance(agent, LlmAgent)
    assert agent.name == "bash_agent"
    mock_bash_tools.assert_called_once_with(
        allowlist=["ls", "pwd"],
        blacklist=["rm"],
    )


def test_get_agent_uses_provided_allowlist_blacklist():
    """get_agent uses allowed_commands and blacklisted_commands when provided."""
    mock_settings = MagicMock()
    mock_settings.api_key = "key"
    mock_settings.model = "gpt-4o-mini"
    mock_settings.default_allowlist = []
    mock_settings.default_blacklist = []

    with patch("flourish.agent.agents.get_settings", return_value=mock_settings):
        with patch("flourish.agent.agents.get_bash_tools") as mock_bash_tools:
            mock_bash_tools.return_value = []
            agents.get_agent(
                allowed_commands=["ls", "git"],
                blacklisted_commands=["dd"],
            )

    mock_bash_tools.assert_called_once_with(
        allowlist=["ls", "git"],
        blacklist=["dd"],
    )


def test_get_agent_sets_anthropic_key_when_model_anthropic():
    """get_agent sets ANTHROPIC_API_KEY when model starts with anthropic/."""
    mock_settings = MagicMock()
    mock_settings.api_key = "anthropic-key"
    mock_settings.model = "anthropic/claude-3-5-sonnet"
    mock_settings.default_allowlist = []
    mock_settings.default_blacklist = []

    with patch("flourish.agent.agents.get_settings", return_value=mock_settings):
        with patch("flourish.agent.agents.get_bash_tools", return_value=[]):
            mock_environ = MagicMock()
            with patch("flourish.agent.agents.os.environ", mock_environ):
                agents.get_agent()
    mock_environ.setdefault.assert_any_call("ANTHROPIC_API_KEY", "anthropic-key")


def test_get_agent_sets_google_key_when_model_gemini():
    """get_agent sets GOOGLE_API_KEY when model contains gemini."""
    mock_settings = MagicMock()
    mock_settings.api_key = "google-key"
    mock_settings.model = "gemini/gemini-2.0-flash"
    mock_settings.default_allowlist = []
    mock_settings.default_blacklist = []

    with patch("flourish.agent.agents.get_settings", return_value=mock_settings):
        with patch("flourish.agent.agents.get_bash_tools", return_value=[]):
            mock_environ = MagicMock()
            with patch("flourish.agent.agents.os.environ", mock_environ):
                agents.get_agent()
    mock_environ.setdefault.assert_any_call("GOOGLE_API_KEY", "google-key")
