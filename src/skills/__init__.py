"""
Skills System for ASTRO - Plugin architecture for extensibility.

Skills can be:
- Bundled: Built into ASTRO
- Managed: Downloaded from a registry
- Workspace: User-created skills
- Self-Modified: Skills that can modify themselves or create new skills
"""

from .skill import Skill, SkillConfig, SkillContext, SkillResult
from .registry import SkillRegistry
from .manager import SkillManager
from .builtin import register_builtin_skills

__all__ = [
    'Skill',
    'SkillConfig',
    'SkillContext',
    'SkillResult',
    'SkillRegistry',
    'SkillManager',
    'register_builtin_skills',
]
