"""Unit tests for config tools (allowlist/blacklist, is_in_allowlist, is_in_blacklist)."""

from unittest.mock import patch

import pytest

from flouri.tools import globals as globals_module
from flouri.tools.config import config_tools


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset allowlist/blacklist before each test."""
    globals_module.GLOBAL_ALLOWLIST = []
    globals_module.GLOBAL_BLACKLIST = []
    yield
    globals_module.GLOBAL_ALLOWLIST = []
    globals_module.GLOBAL_BLACKLIST = []


@pytest.fixture(autouse=True)
def mock_log_tool_call():
    with patch("flouri.tools.config.config_tools.log_tool_call"):
        yield


def test_add_to_allowlist_when_global_none():
    """add_to_allowlist initializes GLOBAL_ALLOWLIST when None."""
    globals_module.GLOBAL_ALLOWLIST = None
    result = config_tools.add_to_allowlist("ls")
    assert result["status"] == "success"
    assert globals_module.GLOBAL_ALLOWLIST == ["ls"]


def test_add_to_allowlist_config_manager_exception():
    """add_to_allowlist succeeds when ConfigManager raises."""
    globals_module.GLOBAL_ALLOWLIST = []
    with patch("flouri.config.config_manager.ConfigManager", side_effect=RuntimeError("no config")):
        result = config_tools.add_to_allowlist("pwd")
    assert result["status"] == "success"
    assert "pwd" in result["allowlist"]


def test_remove_from_allowlist_when_in_list():
    """remove_from_allowlist removes command and updates config when in list."""
    globals_module.GLOBAL_ALLOWLIST = ["ls", "pwd"]
    with patch("flouri.config.config_manager.ConfigManager") as mock_cm:
        result = config_tools.remove_from_allowlist("pwd")
    assert result["status"] == "success"
    assert globals_module.GLOBAL_ALLOWLIST == ["ls"]
    mock_cm.return_value.remove_from_allowlist.assert_called_once_with("pwd")


def test_remove_from_allowlist_config_manager_exception():
    """remove_from_allowlist succeeds when ConfigManager raises."""
    globals_module.GLOBAL_ALLOWLIST = ["ls"]
    with patch("flouri.config.config_manager.ConfigManager", side_effect=OSError("read-only")):
        result = config_tools.remove_from_allowlist("ls")
    assert result["status"] == "success"
    assert globals_module.GLOBAL_ALLOWLIST == []


def test_add_to_blacklist_when_global_none():
    """add_to_blacklist initializes GLOBAL_BLACKLIST when None."""
    globals_module.GLOBAL_BLACKLIST = None
    result = config_tools.add_to_blacklist("rm")
    assert result["status"] == "success"
    assert globals_module.GLOBAL_BLACKLIST == ["rm"]


def test_add_to_blacklist_config_manager_exception():
    """add_to_blacklist succeeds when ConfigManager raises."""
    globals_module.GLOBAL_BLACKLIST = []
    with patch("flouri.config.config_manager.ConfigManager", side_effect=ImportError("no module")):
        result = config_tools.add_to_blacklist("dd")
    assert result["status"] == "success"
    assert "dd" in result["blacklist"]


def test_remove_from_blacklist_config_manager_exception():
    """remove_from_blacklist succeeds when ConfigManager raises."""
    globals_module.GLOBAL_BLACKLIST = ["rm"]
    with patch("flouri.config.config_manager.ConfigManager", side_effect=RuntimeError("fail")):
        result = config_tools.remove_from_blacklist("rm")
    assert result["status"] == "success"
    assert globals_module.GLOBAL_BLACKLIST == []


def test_is_in_allowlist_empty_command():
    """is_in_allowlist returns error for empty command."""
    result = config_tools.is_in_allowlist("   ")
    assert result["status"] == "error"
    assert result["in_allowlist"] is False
    assert "Empty command" in result["message"]


def test_is_in_allowlist_empty_command_empty_string():
    """is_in_allowlist returns error for empty string."""
    result = config_tools.is_in_allowlist("")
    assert result["status"] == "error"
    assert result["in_allowlist"] is False


def test_is_in_blacklist_empty_command():
    """is_in_blacklist returns error for empty command."""
    result = config_tools.is_in_blacklist("   ")
    assert result["status"] == "error"
    assert result["in_blacklist"] is False
    assert "Empty command" in result["message"]


def test_list_allowlist_when_none():
    """list_allowlist returns empty list when GLOBAL_ALLOWLIST is None."""
    globals_module.GLOBAL_ALLOWLIST = None
    result = config_tools.list_allowlist()
    assert result["status"] == "success"
    assert result["allowlist"] == []
    assert result["count"] == 0


def test_list_blacklist_when_none():
    """list_blacklist returns empty list when GLOBAL_BLACKLIST is None."""
    globals_module.GLOBAL_BLACKLIST = None
    result = config_tools.list_blacklist()
    assert result["status"] == "success"
    assert result["blacklist"] == []
    assert result["count"] == 0
