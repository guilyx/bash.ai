"""Plugin system for bash.ai."""

from .base import Plugin, PluginManager
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
]
