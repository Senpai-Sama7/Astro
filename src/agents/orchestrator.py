"""Sub-agent orchestration for parallel task execution."""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

from .task import Task, TaskResult, TaskStatus


@dataclass
class SubAgent:
    """A specialized sub-agent."""
    id: str
    name: str
    agent_type: str
    system_prompt: str
    skills: List[str] = field(default_factory=list)
    llm_provider: Optional[Any] = None
    max_concurrent_tasks: int = 3
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute a task."""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        try:
            # Build context
            context = f"""You are a specialized sub-agent: {self.name}
{self.system_prompt}

Your task: {task.description}
Inputs: {task.inputs}
"""
            
            if self.llm_provider:
                messages = [
                    {"role": "system", "content": context},
                    {"role": "user", "content": f"Execute this task: {task.description}"}
                ]
                
                response = await self.llm_provider.complete(messages)
                
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                
                return TaskResult.ok(
                    output=response.content,
                    agent_id=self.id,
                    latency_ms=(task.completed_at - task.started_at) * 1000
                )
            else:
                # Fallback: simulate execution
                await asyncio.sleep(1)
                
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                
                return TaskResult.ok(
                    output=f"Simulated execution of: {task.description}",
                    agent_id=self.id
                )
        
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            return TaskResult.error(str(e), agent_id=self.id)


class AgentOrchestrator:
    """Orchestrates multiple sub-agents for parallel execution."""
    
    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider
        self.agents: Dict[str, SubAgent] = {}
        self.tasks: Dict[str, Task] = {}
        self._running = False
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._callbacks: List[Callable[[Task], None]] = []
    
    def create_agent(
        self,
        name: str,
        agent_type: str,
        system_prompt: str,
        skills: Optional[List[str]] = None,
        max_concurrent: int = 3
    ) -> SubAgent:
        """Create a new sub-agent."""
        import uuid
        
        agent = SubAgent(
            id=str(uuid.uuid4())[:8],
            name=name,
            agent_type=agent_type,
            system_prompt=system_prompt,
            skills=skills or [],
            llm_provider=self.llm_provider,
            max_concurrent_tasks=max_concurrent
        )
        
        self.agents[agent.id] = agent
        return agent
    
    def register_callback(self, callback: Callable[[Task], None]):
        """Register callback for task completion."""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self, task: Task):
        """Notify all callbacks."""
        for callback in self._callbacks:
            try:
                callback(task)
            except Exception:
                pass
    
    async def submit_task(
        self,
        description: str,
        agent_type: str = "general",
        inputs: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        parent_id: Optional[str] = None
    ) -> Task:
        """Submit a new task."""
        task = Task.create(
            description=description,
            agent_type=agent_type,
            inputs=inputs or {},
            parent_id=parent_id,
            dependencies=dependencies or []
        )
        
        self.tasks[task.id] = task
        
        # Start execution if ready
        if task.is_ready and not dependencies:
            asyncio.create_task(self._execute_task(task, agent_id))
        
        return task
    
    async def _execute_task(self, task: Task, agent_id: Optional[str] = None):
        """Execute a single task."""
        # Find suitable agent
        agent = None
        
        if agent_id and agent_id in self.agents:
            agent = self.agents[agent_id]
        else:
            # Find agent by type
            for a in self.agents.values():
                if a.agent_type == task.agent_type:
                    agent = a
                    break
            
            # Fallback to first agent
            if not agent and self.agents:
                agent = list(self.agents.values())[0]
        
        if not agent:
            task.status = TaskStatus.FAILED
            task.result = TaskResult.error("No suitable agent found")
            self._notify_callbacks(task)
            return
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                agent.execute(task),
                timeout=task.max_duration
            )
            task.result = result
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.result = TaskResult.error(f"Task timed out after {task.max_duration}s")
        
        self._notify_callbacks(task)
        
        # Check for dependent tasks
        await self._check_dependent_tasks(task)
    
    async def _check_dependent_tasks(self, completed_task: Task):
        """Check and trigger dependent tasks."""
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and completed_task.id in task.dependencies:
                # Check if all dependencies are done
                all_done = all(
                    self.tasks[dep_id].is_done
                    for dep_id in task.dependencies
                    if dep_id in self.tasks
                )
                
                if all_done:
                    asyncio.create_task(self._execute_task(task))
    
    async def execute_parallel(
        self,
        descriptions: List[str],
        agent_type: str = "general",
        max_parallel: int = 5
    ) -> List[TaskResult]:
        """Execute multiple tasks in parallel."""
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def run_with_limit(desc: str) -> TaskResult:
            async with semaphore:
                task = await self.submit_task(desc, agent_type)
                # Wait for completion
                while not task.is_done:
                    await asyncio.sleep(0.1)
                return task.result
        
        results = await asyncio.gather(*[
            run_with_limit(desc) for desc in descriptions
        ])
        
        return results
    
    async def execute_workflow(
        self,
        tasks_config: List[Dict[str, Any]]
    ) -> Dict[str, Task]:
        """Execute a workflow of dependent tasks."""
        created_tasks = {}
        
        # Create all tasks
        for config in tasks_config:
            task = Task.create(
                description=config["description"],
                agent_type=config.get("agent_type", "general"),
                inputs=config.get("inputs", {}),
                dependencies=config.get("dependencies", [])
            )
            
            self.tasks[task.id] = task
            created_tasks[config.get("id", task.id)] = task
        
        # Start tasks that have no dependencies
        for task in created_tasks.values():
            if not task.dependencies:
                asyncio.create_task(self._execute_task(task))
        
        return created_tasks
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get task status."""
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Dict]:
        """List all tasks."""
        tasks = self.tasks.values()
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        return [t.to_dict() for t in tasks]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        task = self.tasks.get(task_id)
        
        if task and not task.is_done:
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()
            return True
        
        return False
    
    def get_agent_stats(self) -> Dict[str, Dict]:
        """Get statistics for all agents."""
        stats = {}
        
        for agent_id, agent in self.agents.items():
            agent_tasks = [t for t in self.tasks.values() if t.result and t.result.metadata.get("agent_id") == agent_id]
            
            stats[agent_id] = {
                "name": agent.name,
                "type": agent.agent_type,
                "total_tasks": len(agent_tasks),
                "completed": len([t for t in agent_tasks if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in agent_tasks if t.status == TaskStatus.FAILED])
            }
        
        return stats
