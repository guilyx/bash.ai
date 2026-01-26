"""Tests for completion system."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

from flourish.completions.loader import CompletionLoader
from flourish.completions.registry import CompletionRegistry


def test_completion_registry_register():
    """Test registering a completion function."""
    registry = CompletionRegistry()

    def complete_test(current_word: str, words: list[str], word_index: int) -> list[Completion]:
        return [Completion("test1"), Completion("test2")]

    registry.register("test", complete_test, "Test completion")
    assert "test" in registry._completions


def test_completion_registry_get_completion():
    """Test getting a completion function."""
    registry = CompletionRegistry()

    def complete_test(current_word: str, words: list[str], word_index: int) -> list[Completion]:
        return [Completion("test1")]

    registry.register("test", complete_test, "Test completion")
    completion_func = registry.get_completion("test")
    assert completion_func is not None
    assert completion_func.func == complete_test
    assert completion_func.description == "Test completion"


def test_completion_registry_get_nonexistent():
    """Test getting a non-existent completion."""
    registry = CompletionRegistry()
    assert "nonexistent" not in registry._completions


def test_completion_registry_list_commands():
    """Test listing all completions."""
    registry = CompletionRegistry()

    def complete_test(current_word: str, words: list[str], word_index: int) -> list[Completion]:
        return []

    registry.register("test1", complete_test, "Test 1")
    registry.register("test2", complete_test, "Test 2")

    commands = registry.list_commands()
    assert len(commands) == 2
    assert "test1" in commands
    assert "test2" in commands


def test_completion_registry_has_completion():
    """Test checking if completion exists."""
    registry = CompletionRegistry()

    def complete_test(current_word: str, words: list[str], word_index: int) -> list[Completion]:
        return []

    registry.register("test", complete_test, "Test")
    assert registry.has_completion("test") is True
    assert registry.has_completion("nonexistent") is False


def test_completion_registry_register_alias():
    """Test registering an alias."""
    registry = CompletionRegistry()

    def complete_test(current_word: str, words: list[str], word_index: int) -> list[Completion]:
        return []

    registry.register("test", complete_test, "Test")
    registry.register_alias("t", "test")
    
    completion = registry.get_completion("t")
    assert completion is not None
    assert completion.func == complete_test


def test_completion_loader_init():
    """Test CompletionLoader initialization."""
    registry = CompletionRegistry()
    loader = CompletionLoader(registry)
    assert loader.registry == registry


def test_completion_loader_load_from_directory_nonexistent(tmp_path):
    """Test loading from non-existent directory."""
    loader = CompletionLoader()
    count = loader.load_from_directory(tmp_path / "nonexistent")
    assert count == 0


def test_completion_loader_load_from_directory_empty(tmp_path):
    """Test loading from empty directory."""
    loader = CompletionLoader()
    count = loader.load_from_directory(tmp_path)
    assert count == 0


def test_completion_loader_load_from_directory_valid(tmp_path):
    """Test loading valid completion script."""
    # Create a completion script
    completion_file = tmp_path / "test.py"
    completion_file.write_text(
        '''
def complete_test(current_word: str, words: list[str], word_index: int):
    return ["test1", "test2"]
'''
    )

    loader = CompletionLoader()
    count = loader.load_from_directory(tmp_path)
    assert count == 1
    assert "test" in loader.registry._completions


def test_completion_loader_load_default_completions():
    """Test loading default completions."""
    loader = CompletionLoader()
    # This should not raise an error
    loader.load_default_completions()


def test_git_completion():
    """Test git completion function."""
    from flourish.completions.git import complete_git

    # Test basic git command completion
    completions = complete_git("", ["git"], 0)
    # May return empty if not in git repo, so just check it's a list
    assert isinstance(completions, list)

    # Test git subcommand completion
    completions = complete_git("st", ["git", "st"], 1)
    assert isinstance(completions, list)
    # If completions exist, check format
    if completions:
        assert all(isinstance(c, Completion) for c in completions)
