"""Builtin skills for ASTRO."""

from .file_skill import FileSkill
from .shell_skill import ShellSkill
from .skill_creator import SkillCreatorSkill
from .browser_skill import BrowserSkill
from .scheduler_skill import SchedulerSkill


def register_builtin_skills(skill_manager):
    """Register all builtin skills."""
    registry = skill_manager.registry
    skills = [
        FileSkill(),
        ShellSkill(),
        SkillCreatorSkill(skill_manager=skill_manager),
        BrowserSkill(),
        SchedulerSkill(),
    ]
    
    for skill in skills:
        registry.register(skill)
