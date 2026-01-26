"""Tests for plugin system."""

import pytest

from flourish.plugins import Plugin, PluginManager, ZshBindingsPlugin
from flourish.plugins.enhancers import (
    CdEnhancementPlugin,
    CommandEnhancer,
    EnhancerManager,
    LsColorEnhancer,
)


class TestPlugin(Plugin):
    """Test plugin for testing."""

    def name(self) -> str:
        return "test_plugin"

    def should_handle(self, command: str) -> bool:
        return command.strip() == "test"

    async def execute(self, command: str, cwd: str) -> dict:
        return {
            "handled": True,
            "output": "test output",
            "exit_code": 0,
        }


@pytest.mark.asyncio
async def test_plugin_manager_register():
    """Test registering a plugin."""
    manager = PluginManager()
    plugin = TestPlugin()
    manager.register(plugin)
    assert len(manager.plugins) == 1


@pytest.mark.asyncio
async def test_plugin_manager_execute():
    """Test executing a command through plugin manager."""
    manager = PluginManager()
    plugin = TestPlugin()
    manager.register(plugin)

    result = await manager.execute("test", "/tmp")
    assert result is not None
    assert result["handled"] is True
    assert result["output"] == "test output"


@pytest.mark.asyncio
async def test_plugin_manager_no_handler():
    """Test plugin manager when no plugin handles the command."""
    manager = PluginManager()
    plugin = TestPlugin()
    manager.register(plugin)

    result = await manager.execute("unknown", "/tmp")
    assert result is None


@pytest.mark.asyncio
async def test_zsh_bindings_plugin_cd_alone(tmp_path):
    """Test ZshBindingsPlugin with 'cd' alone."""
    plugin = ZshBindingsPlugin()
    assert plugin.should_handle("cd") is True

    result = await plugin.execute("cd", str(tmp_path))
    assert result["handled"] is True
    assert result["exit_code"] == 0
    assert "new_cwd" in result


@pytest.mark.asyncio
async def test_zsh_bindings_plugin_cd_dots(tmp_path):
    """Test ZshBindingsPlugin with 'cd ...'."""
    plugin = ZshBindingsPlugin()
    assert plugin.should_handle("cd ...") is True

    # Create nested directories
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)

    result = await plugin.execute("cd ...", str(nested))
    assert result["handled"] is True
    assert result["exit_code"] == 0
    assert "new_cwd" in result


@pytest.mark.asyncio
async def test_zsh_bindings_plugin_should_not_handle():
    """Test ZshBindingsPlugin with commands it shouldn't handle."""
    plugin = ZshBindingsPlugin()
    assert plugin.should_handle("ls") is False
    assert plugin.should_handle("cd /tmp") is False
    assert plugin.should_handle("cd ..") is False


def test_ls_color_enhancer_name():
    """Test LsColorEnhancer name."""
    enhancer = LsColorEnhancer()
    assert enhancer.name() == "ls_color"


def test_ls_color_enhancer_should_enhance():
    """Test LsColorEnhancer should_enhance."""
    enhancer = LsColorEnhancer()
    assert enhancer.should_enhance("ls") is True
    assert enhancer.should_enhance("ls -la") is True
    assert enhancer.should_enhance("lsblk") is False


def test_ls_color_enhancer_enhance_output(tmp_path):
    """Test LsColorEnhancer enhance_output."""
    enhancer = LsColorEnhancer()
    result = enhancer.enhance_output(
        "ls", "file1.txt\ndir1", "", 0, str(tmp_path)
    )
    assert result["enhanced"] is True
    assert "stdout" in result


def test_cd_enhancement_plugin_name():
    """Test CdEnhancementPlugin name."""
    plugin = CdEnhancementPlugin()
    assert plugin.name() == "cd_enhancement"


def test_cd_enhancement_plugin_should_enhance():
    """Test CdEnhancementPlugin should_enhance."""
    plugin = CdEnhancementPlugin()
    assert plugin.should_enhance("cd /tmp") is True
    assert plugin.should_enhance("ls") is False


def test_cd_enhancement_plugin_enhance_output(tmp_path):
    """Test CdEnhancementPlugin enhance_output."""
    plugin = CdEnhancementPlugin()
    result = plugin.enhance_output(
        "cd nonexistent", "", "No such file", 1, str(tmp_path)
    )
    assert "hints" in result


def test_enhancer_manager_register():
    """Test registering an enhancer."""
    manager = EnhancerManager()
    enhancer = LsColorEnhancer()
    manager.register(enhancer)
    assert len(manager.enhancers) == 1


def test_enhancer_manager_enhance():
    """Test enhancer manager enhance method."""
    manager = EnhancerManager()
    enhancer = LsColorEnhancer()
    manager.register(enhancer)

    result = manager.enhance("ls", "output", "", 0, "/tmp")
    assert "stdout" in result
    assert "stderr" in result
    assert "hints" in result
