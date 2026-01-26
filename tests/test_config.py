"""Tests for configuration management."""

import pytest

from flourish.config.config import get_settings


def test_settings_requires_api_key(monkeypatch):
    """Test that settings require API_KEY."""
    monkeypatch.delenv("API_KEY", raising=False)

    # Reset global settings
    import flourish.config.config

    flourish.config.config._settings = None

    with pytest.raises(ValueError, match="API_KEY"):
        get_settings()


def test_settings_loads_from_env(monkeypatch):
    """Test that settings load from environment variables."""
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("MODEL", "gpt-4o-mini")

    # Reset global settings
    import flourish.config.config

    flourish.config.config._settings = None

    settings = get_settings()
    assert settings.api_key == "test-key"
    assert settings.model == "gpt-4o-mini"
