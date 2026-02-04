"""Unit tests for ConfigManager skills API and migration."""

import json

import pytest

from flouri.config.config_manager import ConfigManager


@pytest.fixture
def config_manager(tmp_path):
    """ConfigManager with temporary config file."""
    config_file = tmp_path / "config.json"
    return ConfigManager(config_file=str(config_file))


def test_migrate_from_commands_json_success(tmp_path):
    """_migrate_from_commands_json creates config.json with skills and plugins."""
    old_path = tmp_path / "commands.json"
    new_path = tmp_path / "config.json"
    old_path.write_text(
        json.dumps({"allowlist": ["ls"], "blacklist": ["rm"], "model": "gpt-4o-mini"})
    )

    cm = ConfigManager(config_file=str(tmp_path / "other.json"))
    cm._migrate_from_commands_json(old_path, new_path)

    assert new_path.exists()
    data = json.loads(new_path.read_text())
    assert data["allowlist"] == ["ls"]
    assert data["blacklist"] == ["rm"]
    assert "bash" in data["skills"]["enabled"]
    assert "zsh_bindings" in data["plugins"]["enabled"]


def test_migrate_from_commands_json_failure_uses_defaults(tmp_path):
    """When migration fails (invalid JSON), new file is not created."""
    old_path = tmp_path / "commands.json"
    new_path = tmp_path / "config.json"
    old_path.write_text("invalid json {")

    cm = ConfigManager(config_file=str(tmp_path / "other.json"))
    cm._migrate_from_commands_json(old_path, new_path)
    assert not new_path.exists()


def test_get_enabled_skills_default(config_manager):
    """Default config has default skills enabled."""
    skills = config_manager.get_enabled_skills()
    assert "bash" in skills
    assert "config" in skills
    assert "history" in skills
    assert "system" in skills
    assert "tool_manager" in skills


def test_set_enabled_skills(config_manager):
    """set_enabled_skills overwrites and persists."""
    config_manager.set_enabled_skills(["bash", "ros2"])
    assert config_manager.get_enabled_skills() == ["bash", "ros2"]
    # Reload from file
    cm2 = ConfigManager(config_file=str(config_manager.config_path))
    assert cm2.get_enabled_skills() == ["bash", "ros2"]


def test_add_skill(config_manager):
    """add_skill appends and persists."""
    config_manager.set_enabled_skills(["bash"])
    config_manager.add_skill("ros2")
    assert set(config_manager.get_enabled_skills()) == {"bash", "ros2"}
    config_manager.add_skill("bash")  # no duplicate
    assert config_manager.get_enabled_skills().count("bash") == 1


def test_remove_skill(config_manager):
    """remove_skill removes and persists."""
    config_manager.set_enabled_skills(["bash", "config", "history"])
    config_manager.remove_skill("config")
    assert "config" not in config_manager.get_enabled_skills()
    assert "bash" in config_manager.get_enabled_skills()


def test_load_config_migrates_tools_to_skills(tmp_path):
    """Loading config with tools.enabled but no skills.enabled sets default skills."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "allowlist": [],
                "blacklist": [],
                "tools": {"enabled": ["execute_bash", "get_user"]},
                "plugins": {"enabled": []},
            }
        )
    )
    cm = ConfigManager(config_file=str(config_file))
    # Should have migrated to default skills
    skills = cm.get_enabled_skills()
    assert "bash" in skills
    assert "config" in skills
    # In-memory config drops "tools" (not re-saved to file until next write)
    assert "tools" not in cm.get_config()


def test_load_config_drops_tools_section(tmp_path):
    """Loading config with tools section drops it from in-memory config."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "allowlist": [],
                "blacklist": [],
                "skills": {"enabled": ["bash"]},
                "tools": {"enabled": ["execute_bash"]},
                "plugins": {"enabled": []},
            }
        )
    )
    cm = ConfigManager(config_file=str(config_file))
    assert cm.get_config().get("tools") is None
    assert cm.get_enabled_skills() == ["bash"]
