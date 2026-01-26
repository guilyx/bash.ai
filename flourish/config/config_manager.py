"""Configuration file management for Flourish."""

import json
from pathlib import Path
from typing import Any

from .config import get_settings


class ConfigManager:
    """Manages persistent configuration for Flourish."""

    def __init__(self, config_file: str | None = None):
        """Initialize config manager.

        Args:
            config_file: Optional path to config file. Defaults to ~/.config/flourish/commands.json
        """
        if config_file:
            self.config_path = Path(config_file)
        else:
            # Try project config first, then user config
            project_config = Path(__file__).parent.parent.parent / "config" / "commands.json"
            if project_config.exists():
                self.config_path = project_config
            else:
                config_dir = Path.home() / ".config" / "flourish"
                config_dir.mkdir(parents=True, exist_ok=True)
                self.config_path = config_dir / "commands.json"

        self._config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config: dict[str, Any] = json.load(f)
                    return config
            except (OSError, json.JSONDecodeError):
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> dict[str, Any]:
        """Return default configuration."""
        try:
            settings = get_settings()
            return {
                "allowlist": getattr(settings, "default_allowlist", []),
                "blacklist": getattr(settings, "default_blacklist", ["rm", "dd", "format", "mkfs"]),
                "model": settings.model,
            }
        except (ValueError, AttributeError):
            # If settings can't be loaded (e.g., no API key), return minimal defaults
            return {
                "allowlist": [],
                "blacklist": ["rm", "dd", "format", "mkfs", "chmod 777"],
                "model": "gemini-2.0-flash",
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
