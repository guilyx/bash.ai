"""Tests for configuration management."""


import pytest

from bash_ai.config.config import get_settings


def test_settings_requires_api_key(monkeypatch):
    """Test that settings require GOOGLE_API_KEY."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    # Reset global settings
    import bash_ai.config.config

    bash_ai.config._settings = None

    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        get_settings()


def test_settings_loads_from_env(monkeypatch):
    """Test that settings load from environment variables."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")

    # Reset global settings
    import bash_ai.config.config

    bash_ai.config._settings = None

    settings = get_settings()
    assert settings.google_api_key == "test-key"
    assert settings.model == "gemini-test"
