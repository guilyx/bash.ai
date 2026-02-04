"""Unit tests for flourish.tools (get_enabled_tool_names, get_bash_tools)."""

from unittest.mock import MagicMock, patch

import pytest

from flourish.tools import get_bash_tools, get_enabled_tool_names


def test_get_enabled_tool_names_fallback_on_config_error():
    """get_enabled_tool_names returns all registry tool names when ConfigManager fails."""
    mock_registry = MagicMock()
    mock_registry.get_all_tool_names.return_value = ["execute_bash", "get_user"]
    with patch("flourish.config.config_manager.ConfigManager", side_effect=RuntimeError("config load failed")):
        with patch("flourish.tools.get_registry", return_value=mock_registry):
            result = get_enabled_tool_names()
    assert result == ["execute_bash", "get_user"]


def test_get_bash_tools_with_explicit_enabled_tools():
    """get_bash_tools uses enabled_tools when provided instead of config."""
    with patch("flourish.tools.get_registry") as mock_get_reg:
        mock_reg = mock_get_reg.return_value
        mock_reg.get_enabled_tools.return_value = []
        result = get_bash_tools(
            allowlist=["ls"],
            blacklist=["rm"],
            enabled_tools=["execute_bash", "get_user"],
        )
    mock_reg.get_enabled_tools.assert_called_once_with(["execute_bash", "get_user"])
    assert result == []
