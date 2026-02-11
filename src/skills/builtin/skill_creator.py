"""Skill that can create and modify other skills - enables self-modification."""

from pathlib import Path
from typing import Dict, Any

from ..skill import SkillConfig, SkillContext, SkillResult, SkillPermission, SelfModifyingSkill


class SkillCreatorSkill(SelfModifyingSkill):
    """Skill for creating and managing other skills."""
    
    SKILL_TEMPLATE = '''"""
{description}
"""

from src.skills import Skill, SkillConfig, SkillContext, SkillResult, SkillPermission


class {class_name}(Skill):
    """{description}"""
    
    def __init__(self):
        config = SkillConfig(
            name="{name}",
            description="{description}",
            version="{version}",
            permissions=[{permissions}],
            icon="{icon}"
        )
        super().__init__(config)
    
    def get_parameter_schema(self) -> dict:
        return {schema}
    
    async def execute(self, params: dict, context: SkillContext) -> SkillResult:
{implementation}
'''
    
    def __init__(self):
        config = SkillConfig(
            name="skill_creator",
            description="Create, modify, and manage skills",
            permissions=[SkillPermission.SELF_MODIFY, SkillPermission.FILE_SYSTEM],
            icon="✨"
        )
        super().__init__(config)
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "modify", "list", "delete", "get_code"],
                    "description": "Action to perform"
                },
                "name": {
                    "type": "string",
                    "description": "Skill name"
                },
                "description": {
                    "type": "string",
                    "description": "Skill description (for create)"
                },
                "code": {
                    "type": "string",
                    "description": "Python code for skill (for create/modify)"
                },
                "permissions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of permissions",
                    "default": ["read_only"]
                }
            },
            "required": ["action", "name"]
        }
    
    async def execute(self, params: Dict[str, Any], context: SkillContext) -> SkillResult:
        action = params.get("action")
        _name = params.get("name")
        
        if action == "create":
            return await self._create_skill(params, context)
        elif action == "modify":
            return await self._modify_skill(params, context)
        elif action == "list":
            return self._list_skills(context)
        elif action == "delete":
            return await self._delete_skill(params, context)
        elif action == "get_code":
            return self._get_skill_code(params, context)
        else:
            return SkillResult.error(f"Unknown action: {action}")
    
    async def _create_skill(self, params: Dict, context: SkillContext) -> SkillResult:
        """Create a new skill."""
        name = params.get("name")
        description = params.get("description", f"Skill: {name}")
        code = params.get("code")
        permissions = params.get("permissions", ["read_only"])
        
        if not code:
            # Generate from description using LLM if available
            if self.skill_manager and context.llm_provider:
                result = await self.skill_manager.create_skill_from_description(
                    description, name, context
                )
                return result
            else:
                return SkillResult.error("Code required or LLM provider not available")
        
        # Create skill config
        config = SkillConfig(
            name=name,
            description=description,
            permissions=[SkillPermission(p) for p in permissions],
            source_type="workspace"
        )
        
        # Save and load
        try:
            skill_path = self.registry.save_workspace_skill(config, code)
            skill = await self.skill_manager.load_skill_from_file(skill_path)
            
            return SkillResult.ok(
                f"Created skill '{name}'",
                data={"skill": skill.to_dict(), "path": str(skill_path)}
            )
        except Exception as e:
            return SkillResult.error(f"Failed to create skill: {e}")
    
    async def _modify_skill(self, params: Dict, context: SkillContext) -> SkillResult:
        """Modify an existing skill."""
        name = params.get("name")
        new_code = params.get("code")
        
        if not new_code:
            return SkillResult.error("Code required for modification")
        
        # Check if skill exists
        skill = self.registry.get(name)
        if not skill:
            return SkillResult.error(f"Skill '{name}' not found")
        
        # Get current path
        skill_path = skill.config.source_path
        if not skill_path:
            return SkillResult.error("Cannot modify builtin skills directly")
        
        try:
            # Backup old code
            backup_path = str(skill_path) + ".backup"
            import shutil
            shutil.copy(skill_path, backup_path)
            
            # Write new code
            Path(skill_path).write_text(new_code)
            
            # Reload skill
            self.registry.unregister(name)
            await self.skill_manager.load_skill_from_file(Path(skill_path))
            
            return SkillResult.ok(
                f"Modified skill '{name}'",
                data={"path": skill_path, "backup": backup_path}
            )
        except Exception as e:
            return SkillResult.error(f"Failed to modify skill: {e}")
    
    def _list_skills(self, context: SkillContext) -> SkillResult:
        """List all skills."""
        skills = self.registry.list_skills()
        return SkillResult.ok(
            f"Found {len(skills)} skills",
            data={"skills": skills}
        )
    
    async def _delete_skill(self, params: Dict, context: SkillContext) -> SkillResult:
        """Delete a skill."""
        name = params.get("name")
        
        skill = self.registry.get(name)
        if not skill:
            return SkillResult.error(f"Skill '{name}' not found")
        
        if skill.config.source_type == "builtin":
            return SkillResult.error("Cannot delete builtin skills")
        
        try:
            # Remove files
            if skill.config.source_path:
                Path(skill.config.source_path).unlink(missing_ok=True)
                Path(skill.config.source_path).with_suffix('.json').unlink(missing_ok=True)
            
            # Unregister
            self.registry.unregister(name)
            
            return SkillResult.ok(f"Deleted skill '{name}'")
        except Exception as e:
            return SkillResult.error(f"Failed to delete skill: {e}")
    
    def _get_skill_code(self, params: Dict, context: SkillContext) -> SkillResult:
        """Get skill source code."""
        name = params.get("name")
        
        code = self.registry.load_skill_code(name)
        if not code:
            return SkillResult.error(f"Could not load code for skill '{name}'")
        
        metadata = self.registry.get_skill_metadata(name)
        
        return SkillResult.ok(
            f"Loaded code for '{name}'",
            data={"code": code, "metadata": metadata}
        )
