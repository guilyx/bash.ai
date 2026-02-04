"""Unit tests for flouri.config.config (load_commands_config, Settings)."""

import json
from pathlib import Path
from unittest.mock import patch

from flouri.config import config as config_module


def test_load_commands_config_project_file(tmp_path):
    """load_commands_config reads from project CONFIG_FILE when it exists."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "allowlist": ["ls", "pwd"],
                "blacklist": ["rm"],
                "skills": {"enabled": ["bash"]},
            }
        )
    )
    with patch.object(config_module, "CONFIG_FILE", config_file):
        result = config_module.load_commands_config()
    assert result["allowlist"] == ["ls", "pwd"]
    assert result["blacklist"] == ["rm"]


def test_load_commands_config_user_fallback(tmp_path):
    """load_commands_config falls back to user config when project file missing."""
    user_config = tmp_path / "config.json"
    user_config.write_text(
        json.dumps(
            {
                "allowlist": ["git"],
                "blacklist": [],
            }
        )
    )
    with patch.object(config_module, "CONFIG_FILE", Path("/nonexistent/project/config.json")):
        with patch.object(Path, "home", return_value=tmp_path):
            # user_config_file = tmp_path / ".config" / "flouri" / "config.json"
            user_config_dir = tmp_path / ".config" / "flouri"
            user_config_dir.mkdir(parents=True)
            (user_config_dir / "config.json").write_text(
                json.dumps(
                    {
                        "allowlist": ["git"],
                        "blacklist": [],
                    }
                )
            )
            result = config_module.load_commands_config()
    assert result["allowlist"] == ["git"]


def test_load_commands_config_defaults():
    """load_commands_config returns defaults when no config exists."""
    with patch.object(config_module, "CONFIG_FILE", Path("/nonexistent/config.json")):
        with patch.object(Path, "home") as mock_home:
            mock_home.return_value = Path("/nonexistent_home")
            result = config_module.load_commands_config()
    assert result["allowlist"] == []
    assert "rm" in result["blacklist"]
    assert "dd" in result["blacklist"]


def test_settings_override_allowlist_blacklist_from_env():
    """Settings overrides default_allowlist and default_blacklist from env."""
    with patch.object(
        config_module, "load_commands_config", return_value={"allowlist": ["a"], "blacklist": ["b"]}
    ):
        with patch.dict(
            "os.environ",
            {
                "API_KEY": "sk-test",
                "DEFAULT_ALLOWLIST": "ls, pwd ",
                "DEFAULT_BLACKLIST": " rm , dd ",
            },
        ):
            settings = config_module.Settings()
    assert settings.default_allowlist == ["ls", "pwd"]
    assert settings.default_blacklist == ["rm", "dd"]
