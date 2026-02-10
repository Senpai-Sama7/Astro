"""
Sub-agent orchestration for ASTRO.

Enables spawning specialized sub-agents for parallel task execution.
"""

from .orchestrator import AgentOrchestrator, SubAgent
from .task import Task, TaskResult

__all__ = ['AgentOrchestrator', 'SubAgent', 'Task', 'TaskResult']
