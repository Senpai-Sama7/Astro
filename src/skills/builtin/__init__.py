"""Builtin skills for ASTRO."""

from ..registry import SkillRegistry
from .file_skill import FileSkill
from .shell_skill import ShellSkill
from .skill_creator import SkillCreatorSkill
from .browser_skill import BrowserSkill
from .scheduler_skill import SchedulerSkill


def register_builtin_skills(registry: SkillRegistry):
    """Register all builtin skills."""
    skills = [
        FileSkill(),
        ShellSkill(),
        SkillCreatorSkill(),
        BrowserSkill(),
        SchedulerSkill(),
    ]
    
    for skill in skills:
        registry.register(skill)
