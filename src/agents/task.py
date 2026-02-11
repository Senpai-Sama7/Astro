"""Task definition for sub-agent execution."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid
import time


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Result of task execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def ok(cls, output: Any, **metadata):
        return cls(success=True, output=output, metadata=metadata)
    
    @classmethod
    def failure(cls, error_msg: str, **metadata):
        return cls(success=False, output=None, error=error_msg, metadata=metadata)


@dataclass
class Task:
    """A task to be executed by a sub-agent."""
    id: str
    description: str
    agent_type: str
    inputs: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    max_duration: float = 300.0  # 5 minutes default
    
    @classmethod
    def create(
        cls,
        description: str,
        agent_type: str = "general",
        inputs: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        max_duration: float = 300.0
    ) -> 'Task':
        return cls(
            id=str(uuid.uuid4())[:8],
            description=description,
            agent_type=agent_type,
            inputs=inputs or {},
            parent_id=parent_id,
            dependencies=dependencies or [],
            max_duration=max_duration
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "agent_type": self.agent_type,
            "inputs": self.inputs,
            "status": self.status.value,
            "result": {
                "success": self.result.success if self.result else None,
                "output": self.result.output if self.result else None,
                "error": self.result.error if self.result else None
            } if self.result else None,
            "parent_id": self.parent_id,
            "dependencies": self.dependencies,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.completed_at - self.started_at if self.completed_at and self.started_at else None
        }
    
    @property
    def is_ready(self) -> bool:
        """Check if task is ready to run (dependencies completed)."""
        return self.status == TaskStatus.PENDING
    
    @property
    def is_done(self) -> bool:
        """Check if task is completed, failed, or cancelled."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
