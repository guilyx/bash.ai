"""Completion system for Flouri - bash-completion style."""

from .loader import CompletionLoader
from .registry import CompletionRegistry

__all__ = ["CompletionLoader", "CompletionRegistry"]
