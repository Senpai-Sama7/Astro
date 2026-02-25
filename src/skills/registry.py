"""Skill registry for managing available skills."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from .skill import Skill, SkillConfig


class SkillRegistry:
    """Registry for discovering and managing skills."""
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        self.skills: Dict[str, Skill] = {}
        self.configs: Dict[str, SkillConfig] = {}
        
        # Directories
        self.workspace_dir = workspace_dir or Path.home() / ".astro" / "skills"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.builtin_dir = Path(__file__).parent / "builtin"
        self.managed_dir = Path.home() / ".astro" / "skills" / "managed"
        self.managed_dir.mkdir(parents=True, exist_ok=True)
    
    def register(self, skill: Skill) -> bool:
        """Register a skill."""
        if skill.name in self.skills:
            return False
        
        self.skills[skill.name] = skill
        self.configs[skill.name] = skill.config
        return True
    
    def unregister(self, name: str) -> bool:
        """Unregister a skill."""
        if name in self.skills:
            del self.skills[name]
            del self.configs[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self.skills.get(name)
    
    def get_config(self, name: str) -> Optional[SkillConfig]:
        """Get skill configuration."""
        return self.configs.get(name)
    
    def list_skills(self, filter_permission: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered skills."""
        results = []
        
        for name, skill in self.skills.items():
            if filter_permission:
                from .skill import SkillPermission
                if SkillPermission(filter_permission) not in skill.permissions:
                    continue
            
            results.append(skill.to_dict())
        
        return results
    
    def list_available_in_workspace(self) -> List[str]:
        """List skill files available in workspace."""
        skills = []
        
        if self.workspace_dir.exists():
            for file in self.workspace_dir.glob("*.py"):
                skills.append(file.stem)
        
        return skills
    
    def save_workspace_skill(self, config: SkillConfig, code: str) -> Path:
        """Save a new skill to workspace."""
        # Basic path traversal validation
        if ".." in config.name or "/" in config.name or "\\" in config.name:
            raise ValueError(f"Invalid skill name: {config.name}")

        # Save code
        skill_file = (self.workspace_dir / f"{config.name}.py").resolve()
        if not str(skill_file).startswith(str(self.workspace_dir.resolve())):
            raise ValueError(f"Skill path outside workspace: {skill_file}")

        skill_file.write_text(code)
        
        # Save config
        config_file = self.workspace_dir / f"{config.name}.json"
        config_data = config.to_dict()
        config_data["source_path"] = str(skill_file)
        config_file.write_text(json.dumps(config_data, indent=2))
        
        return skill_file
    
    def load_skill_code(self, name: str) -> Optional[str]:
        """Load skill source code."""
        skill = self.skills.get(name)
        if skill and skill.config.source_path:
            try:
                return Path(skill.config.source_path).read_text()
            except Exception:
                pass
        
        # Try workspace
        skill_file = self.workspace_dir / f"{name}.py"
        if skill_file.exists():
            return skill_file.read_text()
        
        return None
    
    def search_skills(self, query: str) -> List[Dict[str, Any]]:
        """Search skills by name or description."""
        query = query.lower()
        results = []
        
        for name, config in self.configs.items():
            if query in name.lower() or query in config.description.lower():
                results.append(self.skills[name].to_dict())
        
        return results
    
    def get_skill_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get extended metadata about a skill."""
        skill = self.skills.get(name)
        if not skill:
            return None
        
        metadata = skill.to_dict()
        metadata["source_type"] = skill.config.source_type
        metadata["source_path"] = skill.config.source_path
        
        # Add code preview if available
        code = self.load_skill_code(name)
        if code:
            lines = code.split('\n')
            metadata["code_preview"] = '\n'.join(lines[:20]) + ('...' if len(lines) > 20 else '')
            metadata["code_lines"] = len(lines)
        
        return metadata
