"""Task scheduling skill - cron-like functionality."""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict

try:
    from croniter import croniter
    HAS_CRONITER = True
except ImportError:
    HAS_CRONITER = False

from ..skill import Skill, SkillConfig, SkillContext, SkillResult, SkillPermission


@dataclass
class ScheduledTask:
    """A scheduled task."""
    id: str
    name: str
    cron: str  # Cron expression or special strings like "@daily"
    skill_name: str
    skill_params: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0


class SchedulerSkill(Skill):
    """Skill for scheduling automated tasks."""
    
    # Special cron expressions
    SPECIAL_SCHEDULES = {
        "@yearly": "0 0 1 1 *",
        "@monthly": "0 0 1 * *",
        "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *",
        "@hourly": "0 * * * *",
        "@minutely": "* * * * *",
    }
    
    def __init__(self):
        config = SkillConfig(
            name="scheduler",
            description="Schedule tasks to run automatically using cron expressions",
            permissions=[SkillPermission.FILE_SYSTEM],
            icon="⏰"
        )
        super().__init__(config)
        
        self.tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._skill_manager = None
        self._storage_path = Path.home() / ".astro" / "scheduler_tasks.json"
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "remove", "list", "enable", "disable", "run_now"],
                    "description": "Scheduler action"
                },
                "task_id": {
                    "type": "string",
                    "description": "Task ID"
                },
                "name": {
                    "type": "string",
                    "description": "Task name"
                },
                "schedule": {
                    "type": "string",
                    "description": "Cron expression or @daily/@hourly/@weekly"
                },
                "skill_name": {
                    "type": "string",
                    "description": "Skill to execute"
                },
                "skill_params": {
                    "type": "object",
                    "description": "Parameters for skill"
                }
            },
            "required": ["action"]
        }
    
    async def initialize(self) -> bool:
        """Initialize scheduler and load tasks."""
        await super().initialize()
        self._load_tasks()
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        return True
    
    async def shutdown(self):
        """Shutdown scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await super().shutdown()
    
    def set_skill_manager(self, skill_manager):
        """Set skill manager for executing scheduled skills."""
        self._skill_manager = skill_manager
    
    def _load_tasks(self):
        """Load tasks from storage."""
        if self._storage_path.exists():
            try:
                data = json.loads(self._storage_path.read_text())
                for task_data in data.get("tasks", []):
                    task = ScheduledTask(**task_data)
                    self.tasks[task.id] = task
            except Exception as e:
                print(f"Failed to load tasks: {e}")
    
    def _save_tasks(self):
        """Save tasks to storage."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tasks": [asdict(t) for t in self.tasks.values()]
        }
        self._storage_path.write_text(json.dumps(data, indent=2, default=str))
    
    def _get_next_run(self, cron_expr: str) -> Optional[datetime]:
        """Get next run time from cron expression."""
        if not HAS_CRONITER:
            return None
        
        # Handle special expressions
        if cron_expr in self.SPECIAL_SCHEDULES:
            cron_expr = self.SPECIAL_SCHEDULES[cron_expr]
        
        try:
            itr = croniter(cron_expr, datetime.now())
            return itr.get_next(datetime)
        except Exception:
            return None
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                now = datetime.now()
                
                for task in self.tasks.values():
                    if not task.enabled:
                        continue
                    
                    # Check if it's time to run
                    if task.next_run:
                        next_run = datetime.fromisoformat(task.next_run)
                        if now >= next_run:
                            await self._execute_task(task)
                    else:
                        # Calculate next run
                        next_run = self._get_next_run(task.cron)
                        if next_run:
                            task.next_run = next_run.isoformat()
                
                self._save_tasks()
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        print(f"Executing scheduled task: {task.name}")
        
        if self._skill_manager:
            from ..skill import SkillContext
            
            context = SkillContext(
                user_id="scheduler",
                session_id=f"task_{task.id}",
                working_directory=str(Path.home())
            )
            
            try:
                await self._skill_manager.execute_skill(
                    task.skill_name,
                    task.skill_params,
                    context
                )
            except Exception as e:
                print(f"Task execution failed: {e}")
        
        # Update task stats
        task.last_run = datetime.now().isoformat()
        task.run_count += 1
        task.next_run = None  # Will be recalculated
    
    async def execute(self, params: Dict[str, Any], context: SkillContext) -> SkillResult:
        action = params.get("action")
        
        if action == "add":
            return await self._add_task(params, context)
        elif action == "remove":
            return self._remove_task(params, context)
        elif action == "list":
            return self._list_tasks(context)
        elif action == "enable":
            return self._enable_task(params, context, True)
        elif action == "disable":
            return self._enable_task(params, context, False)
        elif action == "run_now":
            return await self._run_now(params, context)
        else:
            return SkillResult.error(f"Unknown action: {action}")
    
    async def _add_task(self, params: Dict, context: SkillContext) -> SkillResult:
        """Add a new scheduled task."""
        if not HAS_CRONITER:
            return SkillResult.error("croniter required. Run: pip install croniter")
        
        name = params.get("name")
        schedule = params.get("schedule")
        skill_name = params.get("skill_name")
        skill_params = params.get("skill_params", {})
        
        if not all([name, schedule, skill_name]):
            return SkillResult.error("name, schedule, and skill_name required")
        
        # Validate cron expression
        if schedule in self.SPECIAL_SCHEDULES:
            cron = self.SPECIAL_SCHEDULES[schedule]
        else:
            cron = schedule
        
        try:
            croniter(cron)
        except Exception as e:
            return SkillResult.error(f"Invalid cron expression: {e}")
        
        # Generate ID
        import hashlib
        task_id = hashlib.md5(f"{name}:{schedule}".encode()).hexdigest()[:8]
        
        # Calculate next run
        next_run = self._get_next_run(cron)
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            cron=cron,
            skill_name=skill_name,
            skill_params=skill_params,
            next_run=next_run.isoformat() if next_run else None
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        return SkillResult.ok(
            f"Added task '{name}' (ID: {task_id})",
            data={"task": asdict(task)}
        )
    
    def _remove_task(self, params: Dict, context: SkillContext) -> SkillResult:
        """Remove a task."""
        task_id = params.get("task_id")
        
        if task_id not in self.tasks:
            return SkillResult.error(f"Task not found: {task_id}")
        
        task = self.tasks.pop(task_id)
        self._save_tasks()
        
        return SkillResult.ok(f"Removed task '{task.name}'")
    
    def _list_tasks(self, context: SkillContext) -> SkillResult:
        """List all tasks."""
        tasks_data = [asdict(t) for t in self.tasks.values()]
        return SkillResult.ok(
            f"Found {len(tasks_data)} tasks",
            data={"tasks": tasks_data}
        )
    
    def _enable_task(self, params: Dict, context: SkillContext, enabled: bool) -> SkillResult:
        """Enable or disable a task."""
        task_id = params.get("task_id")
        
        if task_id not in self.tasks:
            return SkillResult.error(f"Task not found: {task_id}")
        
        self.tasks[task_id].enabled = enabled
        self._save_tasks()
        
        status = "enabled" if enabled else "disabled"
        return SkillResult.ok(f"Task {status}")
    
    async def _run_now(self, params: Dict, context: SkillContext) -> SkillResult:
        """Run a task immediately."""
        task_id = params.get("task_id")
        
        if task_id not in self.tasks:
            return SkillResult.error(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        await self._execute_task(task)
        self._save_tasks()
        
        return SkillResult.ok(f"Executed task '{task.name}'")
