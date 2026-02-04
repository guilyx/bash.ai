"""Unit tests for bash tools (execute_bash, blacklist/allowlist branches)."""

from unittest.mock import MagicMock, patch

import pytest

from flouri.tools import globals as globals_module
from flouri.tools.bash import bash_tools


@pytest.fixture(autouse=True)
def reset_globals():
    globals_module.GLOBAL_ALLOWLIST = ["ls", "pwd"]
    globals_module.GLOBAL_BLACKLIST = []
    globals_module.GLOBAL_CWD = "/tmp"
    yield
    globals_module.GLOBAL_ALLOWLIST = []
    globals_module.GLOBAL_BLACKLIST = []
    globals_module.GLOBAL_CWD = "/tmp"


@pytest.fixture(autouse=True)
def mock_logging():
    with patch("flouri.tools.bash.bash_tools.log_tool_call"):
        with patch("flouri.tools.bash.bash_tools.log_terminal_output"):
            with patch("flouri.tools.bash.bash_tools.log_terminal_error"):
                yield


def test_execute_bash_empty_command():
    """execute_bash returns error for empty command."""
    result = bash_tools.execute_bash("   ")
    assert result["status"] == "error"
    assert "Empty command" in result["message"]


def test_execute_bash_blacklisted():
    """execute_bash returns blocked when command is blacklisted."""
    globals_module.GLOBAL_BLACKLIST = ["rm"]
    result = bash_tools.execute_bash("rm -rf /")
    assert result["status"] == "blocked"
    assert "blacklisted" in result["message"]


def test_execute_bash_allowlist_add_config_manager_exception():
    """execute_bash adds to allowlist and continues when ConfigManager raises."""
    globals_module.GLOBAL_ALLOWLIST = ["ls"]  # "pwd" not in allowlist
    with patch("flouri.config.config_manager.ConfigManager", side_effect=RuntimeError("no config")):
        with patch("flouri.tools.bash.bash_tools.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = ("/home", "")
            mock_popen.return_value = mock_proc
            result = bash_tools.execute_bash("pwd")
    assert result["status"] == "success"
    assert "pwd" in globals_module.GLOBAL_ALLOWLIST


def test_execute_bash_subprocess_exception():
    """execute_bash returns error and logs when subprocess raises."""
    globals_module.GLOBAL_ALLOWLIST = ["true"]
    with patch("flouri.tools.bash.bash_tools.subprocess.Popen", side_effect=OSError("Cannot fork")):
        result = bash_tools.execute_bash("true")
    assert result["status"] == "error"
    assert "message" in result
    assert "true" in result["cmd"]
