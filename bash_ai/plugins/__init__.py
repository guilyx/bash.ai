"""Plugin system for bash.ai."""

from .base import Plugin, PluginManager
from .cd_completer import CdCompleter
from .enhancers import (
    CdEnhancementPlugin,
    CommandEnhancer,
    EnhancerManager,
    LsColorEnhancer,
)
from .zsh_bindings import ZshBindingsPlugin

__all__ = [
    "Plugin",
    "PluginManager",
    "ZshBindingsPlugin",
    "CommandEnhancer",
    "EnhancerManager",
    "LsColorEnhancer",
    "CdEnhancementPlugin",
    "CdCompleter",
]
