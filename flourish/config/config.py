"""Configuration management for Flourish."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default config directory
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
COMMANDS_CONFIG_FILE = CONFIG_DIR / "commands.json"


def load_commands_config() -> dict[str, list[str]]:
    """Load allowlist and blacklist from JSON config file.

    Returns:
        Dictionary with 'allowlist' and 'blacklist' keys
    """
    # First try to load from project config directory
    if COMMANDS_CONFIG_FILE.exists():
        with open(COMMANDS_CONFIG_FILE) as f:
            return json.load(f)

    # Fall back to user config directory
    user_config_file = Path.home() / ".config" / "flourish" / "commands.json"
    if user_config_file.exists():
        with open(user_config_file) as f:
            return json.load(f)

    # Return defaults
    return {
        "allowlist": [],
        "blacklist": ["rm", "dd", "format", "mkfs", "chmod 777"],
    }


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        # Model configuration - supports any LiteLLM provider
        self.model: str = os.getenv("MODEL", "gpt-4o-mini")
        self.api_key: str | None = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError(
                "API_KEY environment variable is required. "
                "Please set it in your .env file or export it."
            )
        self.api_base: str | None = os.getenv("API_BASE")

        # Load commands from JSON config
        commands_config = load_commands_config()
        self.default_allowlist: list[str] = commands_config.get("allowlist", [])
        self.default_blacklist: list[str] = commands_config.get("blacklist", [])

        # Override with environment variables if provided
        if os.getenv("DEFAULT_ALLOWLIST"):
            self.default_allowlist = [
                cmd.strip() for cmd in os.getenv("DEFAULT_ALLOWLIST", "").split(",") if cmd.strip()
            ]
        if os.getenv("DEFAULT_BLACKLIST"):
            self.default_blacklist = [
                cmd.strip() for cmd in os.getenv("DEFAULT_BLACKLIST", "").split(",") if cmd.strip()
            ]

        # Session configuration
        self.app_name: str = os.getenv("APP_NAME", "flourish")
        self.user_id: str = os.getenv("USER_ID", "user")
        self.session_id: str = os.getenv("SESSION_ID", "session")


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the global settings instance.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
