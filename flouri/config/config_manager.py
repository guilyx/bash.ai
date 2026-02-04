"""Configuration file management for Flouri."""

import json
from pathlib import Path
from typing import Any

from .config import get_settings


class ConfigManager:
    """Manages persistent configuration for Flouri."""

    def __init__(self, config_file: str | None = None):
        """Initialize config manager.

        Args:
            config_file: Optional path to config file. Defaults to ~/.config/flouri/config.json
        """
        if config_file:
            self.config_path = Path(config_file)
        else:
            # Try project config first, then user config
            project_config = Path(__file__).parent.parent.parent / "config" / "config.json"
            old_project_config = Path(__file__).parent.parent.parent / "config" / "commands.json"
            if project_config.exists():
                self.config_path = project_config
            else:
                config_dir = Path.home() / ".config" / "flouri"
                config_dir.mkdir(parents=True, exist_ok=True)
                self.config_path = config_dir / "config.json"
                old_user_config = config_dir / "commands.json"
                # Migrate from old commands.json if it exists
                if old_user_config.exists() and not self.config_path.exists():
                    self._migrate_from_commands_json(old_user_config, self.config_path)

        # Migrate from old commands.json in project config if it exists
        if not self.config_path.exists():
            old_project_config = Path(__file__).parent.parent.parent / "config" / "commands.json"
            if old_project_config.exists():
                self._migrate_from_commands_json(old_project_config, self.config_path)

        self._config = self._load_config()

    def _migrate_from_commands_json(self, old_path: Path, new_path: Path):
        """Migrate from old commands.json format to new config.json format.

        Args:
            old_path: Path to old commands.json file
            new_path: Path to new config.json file
        """
        try:
            with open(old_path) as f:
                old_config = json.load(f)

            # Create new config structure (skills enable sets of tools; no tools list)
            new_config = {
                "allowlist": old_config.get("allowlist", []),
                "blacklist": old_config.get("blacklist", []),
                "model": old_config.get("model", "gpt-4o-mini"),
                "skills": {
                    "enabled": [
                        "bash",
                        "config",
                        "history",
                        "system",
                        "tool_manager",
                    ]
                },
                "plugins": {
                    "enabled": [
                        "zsh_bindings",
                        "ls_color",
                        "cd_enhancement",
                    ]
                },
            }

            # Write new config
            new_path.parent.mkdir(parents=True, exist_ok=True)
            with open(new_path, "w") as f:
                json.dump(new_config, f, indent=2)

            # Optionally remove old file (commented out for safety)
            # old_path.unlink()
        except Exception:
            # If migration fails, just use defaults
            pass

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config: dict[str, Any] = json.load(f)
                    # Ensure skills and plugins sections exist
                    if "skills" not in config:
                        config["skills"] = {"enabled": []}
                    if "enabled" not in config["skills"]:
                        config["skills"]["enabled"] = []
                    if not config["skills"]["enabled"] and config.get("tools", {}).get("enabled"):
                        # Migrate: old config had tools.enabled only; use default skills
                        config["skills"]["enabled"] = [
                            "bash",
                            "config",
                            "history",
                            "system",
                            "tool_manager",
                        ]
                    if "plugins" not in config:
                        config["plugins"] = {"enabled": []}
                    # Drop tools section so we only persist skills
                    config.pop("tools", None)
                    return config
            except (OSError, json.JSONDecodeError):
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> dict[str, Any]:
        """Return default configuration."""
        default_skills = ["bash", "config", "history", "system", "tool_manager"]
        default_plugins = ["zsh_bindings", "ls_color", "cd_enhancement"]
        try:
            settings = get_settings()
            return {
                "allowlist": getattr(settings, "default_allowlist", []),
                "blacklist": getattr(settings, "default_blacklist", ["rm", "dd", "format", "mkfs"]),
                "model": settings.model,
                "skills": {"enabled": default_skills},
                "plugins": {"enabled": default_plugins},
            }
        except (ValueError, AttributeError):
            # If settings can't be loaded (e.g., no API key), return minimal defaults
            return {
                "allowlist": [],
                "blacklist": ["rm", "dd", "format", "mkfs", "chmod 777"],
                "model": "gemini-2.0-flash",
                "skills": {"enabled": default_skills},
                "plugins": {"enabled": default_plugins},
            }

    def _save_config(self):
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self._config, f, indent=2)
        except OSError as e:
            raise RuntimeError(f"Failed to save config: {e}") from e

    def get_allowlist(self) -> list[str]:
        """Get current allowlist."""
        allowlist = self._config.get("allowlist", [])
        return list(allowlist) if allowlist else []

    def get_blacklist(self) -> list[str]:
        """Get current blacklist."""
        blacklist = self._config.get("blacklist", [])
        return list(blacklist) if blacklist else []

    def add_to_allowlist(self, command: str):
        """Add a command to the allowlist."""
        allowlist = self.get_allowlist()
        if command not in allowlist:
            allowlist.append(command)
            self._config["allowlist"] = allowlist
            self._save_config()

    def remove_from_allowlist(self, command: str):
        """Remove a command from the allowlist."""
        allowlist = self.get_allowlist()
        if command in allowlist:
            allowlist.remove(command)
            self._config["allowlist"] = allowlist
            self._save_config()

    def add_to_blacklist(self, command: str):
        """Add a command to the blacklist."""
        blacklist = self.get_blacklist()
        if command not in blacklist:
            blacklist.append(command)
            self._config["blacklist"] = blacklist
            self._save_config()

    def remove_from_blacklist(self, command: str):
        """Remove a command from the blacklist."""
        blacklist = self.get_blacklist()
        if command in blacklist:
            blacklist.remove(command)
            self._config["blacklist"] = blacklist
            self._save_config()

    def get_model(self) -> str:
        """Get configured model."""
        model = self._config.get("model", "gemini-2.0-flash")
        return str(model)

    def set_model(self, model: str):
        """Set the model."""
        self._config["model"] = model
        self._save_config()

    def get_config(self) -> dict:
        """Get full configuration."""
        return self._config.copy()

    def get_enabled_plugins(self) -> list[str]:
        """Get list of enabled plugins."""
        plugins_config = self._config.get("plugins", {})
        return list(plugins_config.get("enabled", []))

    def set_enabled_plugins(self, plugins: list[str]):
        """Set the list of enabled plugins."""
        if "plugins" not in self._config:
            self._config["plugins"] = {}
        self._config["plugins"]["enabled"] = list(plugins)
        self._save_config()

    def add_plugin(self, plugin_name: str):
        """Add a plugin to the enabled plugins list."""
        enabled = self.get_enabled_plugins()
        if plugin_name not in enabled:
            enabled.append(plugin_name)
            self.set_enabled_plugins(enabled)

    def remove_plugin(self, plugin_name: str):
        """Remove a plugin from the enabled plugins list."""
        enabled = self.get_enabled_plugins()
        if plugin_name in enabled:
            enabled.remove(plugin_name)
            self.set_enabled_plugins(enabled)

    def get_enabled_skills(self) -> list[str]:
        """Get list of enabled skills."""
        skills_config = self._config.get("skills", {})
        return list(skills_config.get("enabled", []))

    def set_enabled_skills(self, skills: list[str]):
        """Set the list of enabled skills."""
        if "skills" not in self._config:
            self._config["skills"] = {}
        self._config["skills"]["enabled"] = list(skills)
        self._save_config()

    def add_skill(self, skill_name: str):
        """Add a skill to the enabled skills list."""
        enabled = self.get_enabled_skills()
        if skill_name not in enabled:
            enabled.append(skill_name)
            self.set_enabled_skills(enabled)

    def remove_skill(self, skill_name: str):
        """Remove a skill from the enabled skills list."""
        enabled = self.get_enabled_skills()
        if skill_name in enabled:
            enabled.remove(skill_name)
            self.set_enabled_skills(enabled)
