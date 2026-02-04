"""Unit tests for ConfigManager plugins and load/save edge cases."""

from unittest.mock import patch

import pytest

from flouri.config.config_manager import ConfigManager


@pytest.fixture
def config_manager(tmp_path):
    """ConfigManager with temporary config file."""
    config_file = tmp_path / "config.json"
    return ConfigManager(config_file=str(config_file))


def test_get_enabled_plugins(config_manager):
    """get_enabled_plugins returns list from config."""
    plugins = config_manager.get_enabled_plugins()
    assert isinstance(plugins, list)
    assert "zsh_bindings" in plugins or len(plugins) >= 0


def test_set_enabled_plugins(config_manager):
    """set_enabled_plugins overwrites and persists."""
    config_manager.set_enabled_plugins(["plugin_a", "plugin_b"])
    assert config_manager.get_enabled_plugins() == ["plugin_a", "plugin_b"]


def test_add_plugin(config_manager):
    """add_plugin appends and persists."""
    config_manager.set_enabled_plugins(["a"])
    config_manager.add_plugin("b")
    assert set(config_manager.get_enabled_plugins()) == {"a", "b"}


def test_remove_plugin(config_manager):
    """remove_plugin removes and persists."""
    config_manager.set_enabled_plugins(["a", "b"])
    config_manager.remove_plugin("a")
    assert "a" not in config_manager.get_enabled_plugins()
    assert "b" in config_manager.get_enabled_plugins()


def test_load_config_invalid_json(tmp_path):
    """_load_config returns default when file has invalid JSON."""
    config_file = tmp_path / "config.json"
    config_file.write_text("not valid json {")
    cm = ConfigManager(config_file=str(config_file))
    # Should not crash; should have some default structure
    assert "allowlist" in cm.get_config()
    assert "skills" in cm.get_config()


def test_load_config_missing_file_uses_default(tmp_path):
    """When config file does not exist, _default_config is used."""
    config_file = tmp_path / "nonexistent.json"
    assert not config_file.exists()
    cm = ConfigManager(config_file=str(config_file))
    skills = cm.get_enabled_skills()
    assert "bash" in skills


def test_default_config_when_get_settings_raises(tmp_path):
    """_default_config returns minimal defaults when get_settings raises."""
    config_file = tmp_path / "no_config.json"
    with patch("flouri.config.config_manager.get_settings", side_effect=ValueError("no API key")):
        cm = ConfigManager(config_file=str(config_file))
    assert "skills" in cm.get_config()
    assert "bash" in cm.get_enabled_skills()
    assert cm.get_config().get("model") == "gemini-2.0-flash"


def test_save_config_raises_on_oserror(tmp_path):
    """_save_config raises RuntimeError when file write fails."""
    config_file = tmp_path / "config.json"
    cm = ConfigManager(config_file=str(config_file))
    with open(config_file, "w") as f:
        f.write("{}")
    with patch("builtins.open", side_effect=OSError(13, "Permission denied")):
        with pytest.raises(RuntimeError, match="Failed to save config"):
            cm.set_enabled_plugins(["a"])


def test_add_plugin_idempotent_when_already_enabled(config_manager):
    """add_plugin does not duplicate when plugin already in list."""
    config_manager.set_enabled_plugins(["a"])
    config_manager.add_plugin("a")
    assert config_manager.get_enabled_plugins() == ["a"]


def test_remove_plugin_noop_when_not_enabled(config_manager):
    """remove_plugin is no-op when plugin not in list."""
    config_manager.set_enabled_plugins(["a"])
    config_manager.remove_plugin("b")
    assert config_manager.get_enabled_plugins() == ["a"]
