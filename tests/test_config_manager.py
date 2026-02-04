"""Tests for ConfigManager."""

import json

import pytest

from flourish.config.config_manager import ConfigManager


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def config_manager(temp_config_dir):
    """Create a ConfigManager with temporary config directory."""
    config_file = temp_config_dir / "config.json"
    return ConfigManager(config_file=str(config_file))


def test_config_manager_init(config_manager):
    """Test ConfigManager initialization."""
    assert config_manager is not None
    assert config_manager.config_path.exists() or config_manager.config_path.parent.exists()


def test_get_allowlist_empty(config_manager):
    """Test getting allowlist (may have defaults)."""
    allowlist = config_manager.get_allowlist()
    assert isinstance(allowlist, list)


def test_get_blacklist_empty(config_manager):
    """Test getting blacklist (may have defaults)."""
    blacklist = config_manager.get_blacklist()
    assert isinstance(blacklist, list)


def test_add_to_allowlist(config_manager):
    """Test adding command to allowlist."""
    config_manager.add_to_allowlist("ls")
    allowlist = config_manager.get_allowlist()
    assert "ls" in allowlist


def test_add_to_blacklist(config_manager):
    """Test adding command to blacklist."""
    config_manager.add_to_blacklist("rm")
    blacklist = config_manager.get_blacklist()
    assert "rm" in blacklist


def test_remove_from_allowlist(config_manager):
    """Test removing command from allowlist."""
    config_manager.add_to_allowlist("ls")
    config_manager.remove_from_allowlist("ls")
    allowlist = config_manager.get_allowlist()
    assert "ls" not in allowlist


def test_remove_from_blacklist(config_manager):
    """Test removing command from blacklist."""
    config_manager.add_to_blacklist("rm")
    config_manager.remove_from_blacklist("rm")
    blacklist = config_manager.get_blacklist()
    assert "rm" not in blacklist


def test_persist_config(config_manager):
    """Test that config persists to file."""
    config_manager.add_to_allowlist("ls")
    config_manager.add_to_blacklist("rm")

    # Create new manager instance to test persistence
    new_manager = ConfigManager(config_file=str(config_manager.config_path))
    assert "ls" in new_manager.get_allowlist()
    assert "rm" in new_manager.get_blacklist()


def test_multiple_commands(config_manager):
    """Test adding multiple commands."""
    _ = len(config_manager.get_allowlist())
    config_manager.add_to_allowlist("ls")
    config_manager.add_to_allowlist("cd")
    config_manager.add_to_allowlist("git")

    allowlist = config_manager.get_allowlist()
    # Should have at least the 3 we added (may have more from defaults)
    assert len(allowlist) >= 3
    assert "ls" in allowlist
    assert "cd" in allowlist
    assert "git" in allowlist


def test_load_existing_config(config_manager):
    """Test loading existing config from file."""
    # Manually write config file (skills enable sets of tools; no tools section)
    config_data = {
        "allowlist": ["ls", "cd"],
        "blacklist": ["rm"],
        "skills": {"enabled": ["bash", "config"]},
        "plugins": {"enabled": []},
    }
    with open(config_manager.config_path, "w") as f:
        json.dump(config_data, f)

    # Reload
    config_manager._config = config_manager._load_config()
    assert "ls" in config_manager.get_allowlist()
    assert "rm" in config_manager.get_blacklist()
    assert config_manager.get_enabled_skills() == ["bash", "config"]


def test_get_model(config_manager):
    """Test getting model."""
    model = config_manager.get_model()
    assert isinstance(model, str)


def test_set_model(config_manager):
    """Test setting model."""
    config_manager.set_model("gpt-4")
    assert config_manager.get_model() == "gpt-4"


def test_get_config(config_manager):
    """Test getting full config."""
    config = config_manager.get_config()
    assert isinstance(config, dict)
    assert "allowlist" in config
    assert "blacklist" in config
    assert "skills" in config
    assert "enabled" in config["skills"]
    # Tools are derived from skills; config does not store tools
    assert "tools" not in config


def test_enabled_skills(config_manager):
    """Test getting and setting enabled skills (skills enable sets of tools)."""
    config_manager.set_enabled_skills(["bash", "config"])
    assert config_manager.get_enabled_skills() == ["bash", "config"]

    config_manager.add_skill("history")
    assert set(config_manager.get_enabled_skills()) == {"bash", "config", "history"}

    config_manager.remove_skill("config")
    assert config_manager.get_enabled_skills() == ["bash", "history"]


def test_duplicate_commands(config_manager):
    """Test that duplicate commands are not added."""
    config_manager.add_to_allowlist("ls")
    config_manager.add_to_allowlist("ls")
    allowlist = config_manager.get_allowlist()
    assert allowlist.count("ls") == 1
