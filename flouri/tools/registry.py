"""Skill registry initialization and management.

This module provides the global skill registry and registration of all skills.
Skills are defined in their respective folders (e.g., bash/skill.py, config/skill.py).
"""

from .base import SkillRegistry
from .bash.skill import BashSkill
from .config.skill import ConfigSkill
from .history.skill import HistorySkill
from .ros2.skill import ROS2Skill
from .system.skill import SystemSkill
from .tool_manager.skill import ToolManagerSkill

# Global registry instance
_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    """Get or create the global skill registry.

    Returns:
        The global SkillRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
        _register_all_skills(_registry)
    return _registry


def _register_all_skills(registry: SkillRegistry):
    """Register all skills in the registry.

    This function imports and registers all available skills.
    To add a new skill:
    1. Create a skill class in your skill folder (e.g., my_skill/skill.py)
    2. Import it here
    3. Register it in this function

    Args:
        registry: The SkillRegistry to register skills in
    """
    registry.register(BashSkill())
    registry.register(ConfigSkill())
    registry.register(HistorySkill())
    registry.register(SystemSkill())
    registry.register(ROS2Skill())
    registry.register(ToolManagerSkill())
