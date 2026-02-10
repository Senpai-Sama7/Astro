"""Base skill interface and data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import json


class SkillPermission(Enum):
    """Permission levels for skills."""
    READ_ONLY = "read_only"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    BROWSER = "browser"
    SELF_MODIFY = "self_modify"  # Can modify its own code
    SYSTEM = "system"  # Can execute system commands


@dataclass
class SkillConfig:
    """Configuration for a skill."""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "unknown"
    permissions: List[SkillPermission] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    icon: str = "🔧"
    
    # Source info
    source_type: str = "builtin"  # builtin, managed, workspace
    source_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "permissions": [p.value for p in self.permissions],
            "dependencies": self.dependencies,
            "parameters": self.parameters,
            "icon": self.icon,
            "source_type": self.source_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillConfig':
        return cls(
            name=data["name"],
            description=data["description"],
            version=data.get("version", "1.0.0"),
            author=data.get("author", "unknown"),
            permissions=[SkillPermission(p) for p in data.get("permissions", [])],
            dependencies=data.get("dependencies", []),
            parameters=data.get("parameters", {}),
            icon=data.get("icon", "🔧"),
            source_type=data.get("source_type", "builtin"),
            source_path=data.get("source_path"),
        )


@dataclass
class SkillContext:
    """Context passed to skills during execution."""
    user_id: str
    session_id: str
    working_directory: str
    llm_provider: Optional[Any] = None
    memory: Optional[Dict[str, Any]] = None
    
    # Callbacks for interacting with ASTRO
    send_message: Optional[Callable[[str], None]] = None
    log_action: Optional[Callable[[str, Dict], None]] = None
    
    def get_memory(self, key: str, default=None):
        """Get value from skill memory."""
        if self.memory is None:
            return default
        return self.memory.get(key, default)
    
    def set_memory(self, key: str, value: Any):
        """Set value in skill memory."""
        if self.memory is None:
            self.memory = {}
        self.memory[key] = value


@dataclass
class SkillResult:
    """Result from skill execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    artifacts: List[str] = field(default_factory=list)  # Paths to generated files
    
    @classmethod
    def ok(cls, message: str, data: Optional[Dict] = None, artifacts: Optional[List[str]] = None):
        return cls(
            success=True,
            message=message,
            data=data,
            artifacts=artifacts or []
        )
    
    @classmethod
    def error(cls, message: str, data: Optional[Dict] = None):
        return cls(
            success=False,
            message=message,
            data=data,
            artifacts=[]
        )


class Skill(ABC):
    """Base class for all skills."""
    
    def __init__(self, config: SkillConfig):
        self.config = config
        self._initialized = False
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def permissions(self) -> List[SkillPermission]:
        return self.config.permissions
    
    def has_permission(self, permission: SkillPermission) -> bool:
        """Check if skill has a specific permission."""
        return permission in self.permissions
    
    async def initialize(self) -> bool:
        """Initialize the skill. Override if needed."""
        self._initialized = True
        return True
    
    async def shutdown(self):
        """Cleanup when skill is unloaded. Override if needed."""
        self._initialized = False
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any], context: SkillContext) -> SkillResult:
        """Execute the skill with given parameters."""
        pass
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Return JSON schema for skill parameters."""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize skill info."""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "version": self.config.version,
            "author": self.config.author,
            "permissions": [p.value for p in self.config.permissions],
            "icon": self.config.icon,
            "initialized": self._initialized,
            "parameter_schema": self.get_parameter_schema(),
        }


class SelfModifyingSkill(Skill):
    """Base class for skills that can modify themselves or create new skills."""
    
    def __init__(self, config: SkillConfig, skill_manager=None):
        super().__init__(config)
        self.skill_manager = skill_manager
    
    async def create_skill(self, config: SkillConfig, code: str, context: SkillContext) -> SkillResult:
        """Create a new skill programmatically."""
        if not self.has_permission(SkillPermission.SELF_MODIFY):
            return SkillResult.error("Skill does not have SELF_MODIFY permission")
        
        if self.skill_manager is None:
            return SkillResult.error("Skill manager not available")
        
        try:
            # Save skill code to workspace
            skill_path = self.skill_manager.save_workspace_skill(config, code)
            
            # Register the new skill
            await self.skill_manager.load_skill_from_file(skill_path)
            
            return SkillResult.ok(
                f"Created skill '{config.name}' at {skill_path}",
                data={"skill_path": skill_path, "config": config.to_dict()}
            )
        except Exception as e:
            return SkillResult.error(f"Failed to create skill: {e}")
    
    async def modify_self(self, new_code: str, context: SkillContext) -> SkillResult:
        """Modify this skill's own code."""
        if not self.has_permission(SkillPermission.SELF_MODIFY):
            return SkillResult.error("Skill does not have SELF_MODIFY permission")
        
        try:
            if self.config.source_path:
                with open(self.config.source_path, 'w') as f:
                    f.write(new_code)
                
                return SkillResult.ok(
                    f"Modified skill '{self.name}'",
                    data={"source_path": self.config.source_path}
                )
            else:
                return SkillResult.error("Skill source path not available")
        except Exception as e:
            return SkillResult.error(f"Failed to modify skill: {e}")
