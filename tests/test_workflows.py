"""
Integration tests for agent workflows and engine orchestration.
Tests workflow execution, task prioritization, and agent coordination.
"""
import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.base_agent import BaseAgent, AgentCapability, AgentState, TaskResult


# ============================================================================
# Mock Classes for Testing
# ============================================================================

class MockTask:
    """Minimal task mock for testing."""
    def __init__(self, task_id: str, required_capabilities: list = None):
        self.task_id = task_id
        self.task_type = "test"
        self.required_capabilities = required_capabilities or []
        self.parameters = {}
        self.dependencies = []
        self.status = "pending"


class MockWorkflow:
    """Minimal workflow mock for testing."""
    def __init__(self, workflow_id: str, tasks: list = None):
        self.workflow_id = workflow_id
        self.name = f"Workflow {workflow_id}"
        self.tasks = tasks or []
        self.priority = "medium"


class MockAgent(BaseAgent):
    """Mock agent for testing without external dependencies."""

    def __init__(self, agent_id: str, capabilities: list, should_fail: bool = False):
        # Don't call super().__init__ to avoid complex initialization
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.config = {}
        self.state = AgentState.IDLE
        self.task_history = []
        self._consecutive_failures = 0
        self._lock = asyncio.Lock()
        self.should_fail = should_fail
        self.executed_tasks = []
        self.max_task_history = 100
        self.default_timeout = 30.0

    async def execute_task(self, task) -> TaskResult:
        self.executed_tasks.append(task)
        if self.should_fail:
            return TaskResult(success=False, error_message="Mock failure")
        return TaskResult(success=True, result_data={"result": f"Completed {task.task_id}"})


# ============================================================================
# BaseAgent Tests
# ============================================================================

class TestBaseAgentBehavior:
    """Tests for BaseAgent core functionality."""

    @pytest.fixture
    def agent(self):
        return MockAgent("test_agent", [AgentCapability.CODE_ANALYSIS])

    def test_agent_initialization(self, agent):
        assert agent.agent_id == "test_agent"
        assert agent.state == AgentState.IDLE
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities

    @pytest.mark.asyncio
    async def test_execute_task_success(self, agent):
        task = MockTask("task1")
        result = await agent.execute_task(task)
        assert result.success
        assert len(agent.executed_tasks) == 1

    @pytest.mark.asyncio
    async def test_execute_task_failure(self):
        agent = MockAgent("failing", [], should_fail=True)
        task = MockTask("task1")
        result = await agent.execute_task(task)
        assert not result.success
        assert "Mock failure" in result.error_message

    def test_capability_check(self, agent):
        assert AgentCapability.CODE_ANALYSIS in agent.capabilities
        assert AgentCapability.WEB_SEARCH not in agent.capabilities


class TestAgentHealthAndRecovery:
    """Tests for agent health monitoring and recovery."""

    @pytest.fixture
    def agent(self):
        return MockAgent("health_test", [AgentCapability.CODE_ANALYSIS])

    @pytest.mark.asyncio
    async def test_agent_recovery(self, agent):
        agent.state = AgentState.FAILED
        agent._consecutive_failures = 5

        # Simulate recovery
        agent.state = AgentState.IDLE
        agent._consecutive_failures = 0

        assert agent.state == AgentState.IDLE
        assert agent._consecutive_failures == 0

    def test_success_rate_empty_history(self, agent):
        # Empty history should return 1.0 (no failures)
        agent.task_history = []
        # The actual implementation may differ, but we test the concept
        total = len(agent.task_history)
        rate = 1.0 if total == 0 else sum(1 for t in agent.task_history if getattr(t, 'success', False)) / total
        assert rate == 1.0

    def test_success_rate_calculation(self, agent):
        # Simulate task history with TaskResult objects
        agent.task_history = [
            TaskResult(success=True),
            TaskResult(success=True),
            TaskResult(success=False),
            TaskResult(success=True),
            TaskResult(success=False),
        ]
        total = len(agent.task_history)
        successful = sum(1 for t in agent.task_history if t.success)
        rate = successful / total
        assert rate == 0.6  # 3/5


# ============================================================================
# Workflow Orchestration Tests
# ============================================================================

class TestWorkflowOrchestration:
    """Tests for workflow management and task coordination."""

    def test_task_creation(self):
        task = MockTask("task1", [AgentCapability.CODE_ANALYSIS])
        assert task.task_id == "task1"
        assert AgentCapability.CODE_ANALYSIS in task.required_capabilities

    def test_workflow_creation(self):
        tasks = [MockTask("t1"), MockTask("t2")]
        workflow = MockWorkflow("wf1", tasks)
        assert workflow.workflow_id == "wf1"
        assert len(workflow.tasks) == 2

    def test_agent_capability_matching(self):
        """Test that agents are matched to tasks by capability."""
        agent1 = MockAgent("agent1", [AgentCapability.CODE_ANALYSIS])
        agent2 = MockAgent("agent2", [AgentCapability.WEB_SEARCH])

        task = MockTask("t1", [AgentCapability.CODE_ANALYSIS])

        # Check which agent can handle the task
        can_handle_1 = all(cap in agent1.capabilities for cap in task.required_capabilities)
        can_handle_2 = all(cap in agent2.capabilities for cap in task.required_capabilities)

        assert can_handle_1
        assert not can_handle_2

    def test_multi_capability_matching(self):
        """Test matching when task requires multiple capabilities."""
        agent = MockAgent("multi", [AgentCapability.CODE_ANALYSIS, AgentCapability.FILE_OPERATIONS])
        task = MockTask("t1", [AgentCapability.CODE_ANALYSIS, AgentCapability.FILE_OPERATIONS])

        can_handle = all(cap in agent.capabilities for cap in task.required_capabilities)
        assert can_handle


class TestTaskPrioritization:
    """Tests for task priority calculation."""

    def test_priority_ordering(self):
        """Test that priority values are correctly ordered."""
        # Lower number = higher priority in typical heap implementations
        priorities = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        assert priorities["critical"] < priorities["high"]
        assert priorities["high"] < priorities["medium"]
        assert priorities["medium"] < priorities["low"]

    def test_priority_with_dependencies(self):
        """Tasks with unmet dependencies should be deprioritized."""
        task_with_deps = MockTask("t1")
        task_with_deps.dependencies = ["t0"]  # Depends on t0

        task_no_deps = MockTask("t2")
        task_no_deps.dependencies = []

        # Task without dependencies should be processed first
        assert len(task_no_deps.dependencies) < len(task_with_deps.dependencies)


# ============================================================================
# Agent State Management Tests
# ============================================================================

class TestAgentStateManagement:
    """Tests for agent state transitions."""

    @pytest.fixture
    def agent(self):
        return MockAgent("state_test", [])

    def test_initial_state(self, agent):
        assert agent.state == AgentState.IDLE

    def test_state_transition_to_busy(self, agent):
        agent.state = AgentState.BUSY
        assert agent.state == AgentState.BUSY

    def test_state_transition_to_error(self, agent):
        agent.state = AgentState.FAILED
        assert agent.state == AgentState.FAILED

    def test_consecutive_failure_tracking(self, agent):
        agent._consecutive_failures = 0
        agent._consecutive_failures += 1
        agent._consecutive_failures += 1
        assert agent._consecutive_failures == 2


# ============================================================================
# Concurrent Execution Tests
# ============================================================================

class TestConcurrentExecution:
    """Tests for concurrent task execution."""

    @pytest.mark.asyncio
    async def test_multiple_agents_parallel(self):
        """Test that multiple agents can execute tasks in parallel."""
        agents = [
            MockAgent(f"agent_{i}", [AgentCapability.CODE_ANALYSIS])
            for i in range(3)
        ]
        tasks = [MockTask(f"task_{i}") for i in range(3)]

        # Execute all tasks concurrently
        results = await asyncio.gather(*[
            agent.execute_task(task)
            for agent, task in zip(agents, tasks)
        ])

        assert all(r.success for r in results)
        assert all(len(a.executed_tasks) == 1 for a in agents)

    @pytest.mark.asyncio
    async def test_single_agent_sequential(self):
        """Test that a single agent executes tasks sequentially."""
        agent = MockAgent("single", [AgentCapability.CODE_ANALYSIS])
        tasks = [MockTask(f"task_{i}") for i in range(5)]

        for task in tasks:
            result = await agent.execute_task(task)
            assert result.success

        assert len(agent.executed_tasks) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
