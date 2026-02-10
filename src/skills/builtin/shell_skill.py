"""Shell execution skill with security controls."""

import asyncio
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

from ..skill import Skill, SkillConfig, SkillContext, SkillResult, SkillPermission


class ShellSkill(Skill):
    """Skill for executing shell commands safely."""
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
        (r"^rm\s+-rf\s+/\s*$", "recursive root deletion"),
        (r";\s*rm\s+-rf\s+/", "recursive root deletion"),
        (r">\s*/dev/null.*rm.*-rf", "masked deletion"),
        (r":\(\)\s*\{\s*:\|:&\s*\};:", "fork bomb"),
        (r"rm\s+-rf\s+/\s*\*", "wildcard root deletion"),
        (r"dd\s+if=\S+\s+of=/dev/[sh]d", "disk destruction"),
        (r"mkfs\.\w+\s+/dev/[sh]d", "filesystem destruction"),
        (r">\s*/dev/[sh]d[a-z]?\b", "direct disk write"),
        (r"curl\s+.*\|\s*sh", "pipe to shell"),
        (r"wget\s+.*\|\s*sh", "pipe to shell"),
        (r"bash\s+-c\s+.*\$\(", "command substitution"),
        (r"eval\s*\$", "eval with variable"),
        (r"sudo\s+rm\s+-rf", "sudo recursive deletion"),
    ]
    
    def __init__(self):
        config = SkillConfig(
            name="shell",
            description="Execute shell commands safely",
            permissions=[SkillPermission.SYSTEM],
            icon="💻"
        )
        super().__init__(config)
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds",
                    "default": 30
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for command"
                }
            },
            "required": ["command"]
        }
    
    def _check_command(self, command: str) -> Tuple[bool, str]:
        """Check if command is safe to execute."""
        for pattern, description in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Blocked dangerous command: {description}"
        
        return True, ""
    
    async def execute(self, params: Dict[str, Any], context: SkillContext) -> SkillResult:
        command = params.get("command", "").strip()
        timeout = params.get("timeout", 30)
        cwd = params.get("cwd", context.working_directory)
        
        if not command:
            return SkillResult.error("No command provided")
        
        # Security check
        is_safe, reason = self._check_command(command)
        if not is_safe:
            return SkillResult.error(reason)
        
        try:
            # Execute command
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                
                output = stdout.decode('utf-8', errors='replace')
                errors = stderr.decode('utf-8', errors='replace')
                
                result = {
                    "stdout": output,
                    "stderr": errors,
                    "returncode": proc.returncode
                }
                
                if proc.returncode == 0:
                    return SkillResult.ok(
                        f"Command executed successfully",
                        data=result
                    )
                else:
                    return SkillResult.error(
                        f"Command failed with exit code {proc.returncode}",
                        data=result
                    )
                    
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return SkillResult.error(f"Command timed out after {timeout}s")
                
        except Exception as e:
            return SkillResult.error(f"Command execution failed: {e}")
