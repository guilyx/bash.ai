"""Plugin system for bash.ai."""

from .base import Plugin, PluginManager
from .zsh_bindings import ZshBindingsPlugin

__all__ = ["Plugin", "PluginManager", "ZshBindingsPlugin"]
