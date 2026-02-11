"""Skill manager for loading and executing skills."""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .skill import Skill, SkillConfig, SkillContext, SkillResult
from .registry import SkillRegistry


class SkillManager:
    """Manages skill lifecycle and execution."""
    
    def __init__(self, workspace_dir: Optional[Path] = None, llm_provider=None):
        self.registry = SkillRegistry(workspace_dir)
        self.llm_provider = llm_provider
        self._initialized = False
    
    async def initialize(self):
        """Initialize skill manager and load builtin skills."""
        if self._initialized:
            return
        
        from .builtin import register_builtin_skills
        register_builtin_skills(self.registry)
        
        # Load workspace skills
        await self.load_workspace_skills()
        
        self._initialized = True
    
    async def load_workspace_skills(self):
        """Load all skills from workspace directory."""
        workspace = self.registry.workspace_dir
        
        if not workspace.exists():
            return
        
        for config_file in workspace.glob("*.json"):
            try:
                await self.load_skill_from_config(config_file)
            except Exception as e:
                print(f"Failed to load skill from {config_file}: {e}")
    
    async def load_skill_from_file(self, skill_path: Path) -> Skill:
        """Load a skill from a Python file."""
        config_path = skill_path.with_suffix('.json')
        
        if config_path.exists():
            return await self.load_skill_from_config(config_path)
        
        # Load without config
        return await self._load_skill_module(skill_path, None)
    
    async def load_skill_from_config(self, config_path: Path) -> Skill:
        """Load a skill using its config file."""
        config_data = json.loads(config_path.read_text())
        config = SkillConfig.from_dict(config_data)
        
        # Find the code file
        if config.source_path:
            skill_path = Path(config.source_path)
        else:
            skill_path = config_path.with_suffix('.py')
        
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill code not found: {skill_path}")
        
        return await self._load_skill_module(skill_path, config)
    
    async def _load_skill_module(self, skill_path: Path, config: Optional[SkillConfig]) -> Skill:
        """Load a skill module dynamically."""
        module_name = f"astro_skill_{skill_path.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, skill_path)
        if not spec or not spec.loader:
            raise ImportError(f"Cannot load skill from {skill_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find the skill class
        skill_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Skill) and 
                attr is not Skill):
                skill_class = attr
                break
        
        if not skill_class:
            raise ValueError(f"No Skill subclass found in {skill_path}")
        
        # Create instance
        if config is None:
            config = SkillConfig(
                name=skill_path.stem,
                description=f"Skill loaded from {skill_path.name}",
                source_type="workspace",
                source_path=str(skill_path)
            )
        
        skill = skill_class(config)
        await skill.initialize()
        
        self.registry.register(skill)
        return skill
    
    async def execute_skill(
        self,
        name: str,
        params: Dict[str, Any],
        context: SkillContext
    ) -> SkillResult:
        """Execute a skill with given parameters."""
        skill = self.registry.get(name)
        
        if not skill:
            return SkillResult.error(f"Skill '{name}' not found")
        
        try:
            return await skill.execute(params, context)
        except Exception as e:
            return SkillResult.error(f"Skill execution failed: {e}")
    
    async def create_skill_from_description(
        self,
        description: str,
        name: str,
        context: SkillContext
    ) -> SkillResult:
        """Create a new skill using LLM from description."""
        if not self.llm_provider:
            return SkillResult.error("LLM provider not available")
        
        prompt = f"""Create a Python skill for ASTRO that does the following:

{description}

The skill should:
1. Inherit from Skill base class
2. Have a Config class with name, description, permissions
3. Implement an execute method that takes params and context
4. Return a SkillResult

Use this template:

```python
from src.skills import Skill, SkillConfig, SkillContext, SkillResult, SkillPermission

class {name.title()}Skill(Skill):
    def __init__(self):
        config = SkillConfig(
            name="{name}",
            description="<description>",
            permissions=[SkillPermission.READ_ONLY],  # Adjust as needed
            icon="🔧"
        )
        super().__init__(config)
    
    async def execute(self, params: dict, context: SkillContext) -> SkillResult:
        # Implementation here
        return SkillResult.ok("Success!")
```

Return only the complete Python code, no explanations.
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_provider.complete(messages)
            
            code = response.content
            
            # Extract code from markdown if present
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            # Create the skill
            config = SkillConfig(
                name=name,
                description=description,
                permissions=[],  # Safe defaults
                source_type="workspace"
            )
            
            skill_path = self.registry.save_workspace_skill(config, code)
            skill = await self.load_skill_from_file(skill_path)
            
            return SkillResult.ok(
                f"Created skill '{name}' at {skill_path}",
                data={"skill": skill.to_dict(), "code": code}
            )
            
        except Exception as e:
            return SkillResult.error(f"Failed to create skill: {e}")
    
    def get_skill_help(self, name: Optional[str] = None) -> str:
        """Get help text for skills."""
        if name:
            skill = self.registry.get(name)
            if not skill:
                return f"Skill '{name}' not found."
            
            schema = skill.get_parameter_schema()
            return f"""
{skill.config.icon} **{skill.name}** v{skill.config.version}
{skill.config.description}

Permissions: {', '.join(p.value for p in skill.permissions)}

Parameters Schema:
```json
{json.dumps(schema, indent=2)}
```
"""
        else:
            skills = self.registry.list_skills()
            if not skills:
                return "No skills registered."
            
            lines = ["📦 Available Skills:\n"]
            for skill_info in skills:
                lines.append(f"  {skill_info['icon']} **{skill_info['name']}** - {skill_info['description']}")
            
            return '\n'.join(lines)
