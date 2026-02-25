"""File operations skill."""

from pathlib import Path
from typing import Dict, Any

from ..skill import Skill, SkillConfig, SkillContext, SkillResult, SkillPermission


class FileSkill(Skill):
    """Skill for file system operations."""
    
    def __init__(self):
        config = SkillConfig(
            name="file",
            description="Read, write, and manage files",
            permissions=[SkillPermission.FILE_SYSTEM],
            icon="📁"
        )
        super().__init__(config)
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "list", "exists", "delete", "mkdir"],
                    "description": "File operation to perform"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for write action)"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively",
                    "default": False
                }
            },
            "required": ["action", "path"]
        }
    
    async def execute(self, params: Dict[str, Any], context: SkillContext) -> SkillResult:
        action = params.get("action")
        path_str = params.get("path", "")
        
        # Resolve path relative to working directory
        path = Path(path_str)
        if not path.is_absolute():
            path = Path(context.working_directory) / path
        
        path = path.resolve()
        
        # Security: Check path is within working directory
        try:
            path.relative_to(Path(context.working_directory).resolve())
        except ValueError:
            return SkillResult.error("Access denied: path outside working directory")
        
        try:
            if action == "read":
                if not path.exists():
                    return SkillResult.error(f"File not found: {path}")
                content = path.read_text()
                return SkillResult.ok(f"Read {len(content)} characters", data={"content": content})
            
            elif action == "write":
                content = params.get("content", "")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                return SkillResult.ok(f"Wrote {len(content)} characters to {path}")
            
            elif action == "list":
                if not path.exists():
                    return SkillResult.error(f"Directory not found: {path}")
                
                recursive = params.get("recursive", False)
                items = []
                
                if recursive:
                    for item in path.rglob("*"):
                        items.append({
                            "name": item.name,
                            "path": str(item.relative_to(path)),
                            "type": "directory" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else None
                        })
                else:
                    for item in path.iterdir():
                        items.append({
                            "name": item.name,
                            "type": "directory" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else None
                        })
                
                return SkillResult.ok(f"Found {len(items)} items", data={"items": items})
            
            elif action == "exists":
                exists = path.exists()
                return SkillResult.ok(
                    f"{path} {'exists' if exists else 'does not exist'}",
                    data={"exists": exists}
                )
            
            elif action == "delete":
                if not path.exists():
                    return SkillResult.error(f"File not found: {path}")
                
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                else:
                    path.unlink()
                
                return SkillResult.ok(f"Deleted {path}")
            
            elif action == "mkdir":
                path.mkdir(parents=True, exist_ok=True)
                return SkillResult.ok(f"Created directory {path}")
            
            else:
                return SkillResult.error(f"Unknown action: {action}")
                
        except Exception as e:
            return SkillResult.error(f"File operation failed: {e}")
