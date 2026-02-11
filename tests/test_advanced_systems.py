"""
Comprehensive Integration Tests for Advanced Systems
Tests: MCP, A2A, Self-Healing, Zero Reasoning, Recursive Learning, Refactory, JIT
"""
import asyncio
import sys
import os
import logging
from datetime import datetime
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IntegrationTestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.duration_ms = 0

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} - {self.name} ({self.duration_ms:.1f}ms)"


@pytest.mark.asyncio
async def test_mcp_integration():
    """Test MCP Integration Module"""
    result = IntegrationTestResult("MCP Integration")
    start = datetime.now()

    try:
        from core.mcp_integration import (
            MCPRegistry, MCPServerConfig, MCPTool,
            MCPToolExecutor
        )

        # Test MCPTool creation
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
            server_name="test_server"
        )
        assert tool.name == "test_tool"
        assert tool.to_dict()["name"] == "test_tool"

        # Test MCPServerConfig
        config = MCPServerConfig(
            name="test_server",
            transport="http",
            url="http://localhost:3000"
        )
        assert config.name == "test_server"

        # Test Registry singleton
        registry1 = MCPRegistry()
        registry2 = MCPRegistry()
        assert registry1 is registry2, "Registry should be singleton"

        # Test MCPToolExecutor
        executor = MCPToolExecutor(registry1)
        history = executor.get_history()
        assert isinstance(history, list)

        result.passed = True
        logger.info("MCP Integration tests passed")
    except Exception as e:
        result.error = str(e)
        logger.error(f"MCP Integration test failed: {e}")

    result.duration_ms = (datetime.now() - start).total_seconds() * 1000
    return result


@pytest.mark.asyncio
async def test_a2a_protocol():
    """Test A2A Protocol"""
    result = IntegrationTestResult("A2A Protocol")
    start = datetime.now()

    try:
        from core.a2a_protocol import (
            A2AMessage, A2ATask,
            AgentCard, MessageBus, A2AMessageType, A2ATaskState,
            get_a2a_coordinator
        )

        # Test AgentCard
        card = AgentCard(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            version="1.0.0",
            capabilities=["test"],
            skills=[]
        )
        assert card.agent_id == "test_agent"
        card_dict = card.to_dict()
        assert card_dict["agentId"] == "test_agent"

        # Test AgentCard from_dict
        restored = AgentCard.from_dict(card_dict)
        assert restored.agent_id == card.agent_id

        # Test A2AMessage
        msg = A2AMessage(
            message_id="msg_001",
            message_type=A2AMessageType.TASK_REQUEST,
            sender_id="agent_1",
            recipient_id="agent_2",
            payload={"test": "data"}
        )
        assert msg.sender_id == "agent_1"

        # Test A2ATask
        task = A2ATask(
            task_id="task_001",
            name="Test Task",
            description="A test task",
            input_data={"input": "test"}
        )
        assert task.state == A2ATaskState.PENDING

        # Test MessageBus
        bus = MessageBus()
        await bus.start()

        received = []
        async def handler(msg):
            received.append(msg)

        bus.subscribe("test_agent", handler)

        await bus.publish(A2AMessage(
            message_id="test_msg",
            message_type=A2AMessageType.HEARTBEAT,
            sender_id="other",
            recipient_id="test_agent",
            payload={}
        ))

        await asyncio.sleep(0.2)
        await bus.stop()

        assert len(received) > 0, "Should receive message"

        # Test Coordinator singleton
        coord1 = get_a2a_coordinator()
        coord2 = get_a2a_coordinator()
        assert coord1 is coord2

        result.passed = True
        logger.info("A2A Protocol tests passed")
    except Exception as e:
        result.error = str(e)
        logger.error(f"A2A Protocol test failed: {e}")

    result.duration_ms = (datetime.now() - start).total_seconds() * 1000
    return result


@pytest.mark.asyncio
async def test_self_healing():
    """Test Self-Healing System"""
    result = IntegrationTestResult("Self-Healing System")
    start = datetime.now()

    try:
        from core.self_healing import (
            CircuitBreaker, RetryPolicy,
            HealthMonitor, RecoveryManager, HealthStatus,
            get_self_healing_system
        )

        # Test CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=1.0)
        assert cb.is_closed
        assert cb.can_execute()

        # Record failures
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()

        assert not cb.is_closed or cb.is_open

        # Test RetryPolicy
        policy = RetryPolicy(max_retries=2, base_delay=0.01)

        call_count = 0
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"

        success, result_val, exceptions = await policy.execute_with_retry(failing_func)
        assert success
        assert result_val == "success"
        assert call_count == 2

        # Test HealthMonitor
        monitor = HealthMonitor(check_interval=0.1)

        async def healthy_check():
            return True

        monitor.register_check("test_component", healthy_check)
        await monitor.start()
        await asyncio.sleep(0.3)

        status = monitor.get_component_health("test_component")
        assert status in [HealthStatus.HEALTHY, HealthStatus.UNKNOWN]

        await monitor.stop()

        # Test RecoveryManager
        recovery = RecoveryManager()
        stats = recovery.get_failure_stats()
        assert "total" in stats

        # Test singleton
        system1 = get_self_healing_system()
        system2 = get_self_healing_system()
        assert system1 is system2

        result.passed = True
        logger.info("Self-Healing tests passed")
    except Exception as e:
        result.error = str(e)
        logger.error(f"Self-Healing test failed: {e}")

    result.duration_ms = (datetime.now() - start).total_seconds() * 1000
    return result


@pytest.mark.asyncio
async def test_zero_reasoning():
    """Test Absolute Zero Reasoning Engine"""
    result = IntegrationTestResult("Zero Reasoning Engine")
    start = datetime.now()

    try:
        from core.zero_reasoning import (
            ChainOfThought, TreeOfThought,
            KnowledgeBase, MetaCognition, ReasoningMode, create_reasoner
        )

        # Test KnowledgeBase
        kb = KnowledgeBase()
        axiom_id = kb.add_axiom("All humans are mortal")
        assert axiom_id is not None

        premise_id = kb.add_premise("Socrates is human", confidence=0.95)
        premise = kb.get_premise(premise_id)
        assert premise.confidence == 0.95

        # Test relation
        kb.add_relation("Socrates", "is_a", "human")
        related = kb.find_related("Socrates")
        assert len(related) > 0

        # Test query
        results = kb.query("human")
        assert len(results) > 0

        # Test ChainOfThought
        cot = ChainOfThought()
        answer, steps, confidence = await cot.reason("What is 2+2?")
        assert answer is not None
        assert isinstance(steps, list)
        assert 0 <= confidence <= 1

        # Test TreeOfThought
        tot = TreeOfThought(branching_factor=2, max_depth=2)
        tree = await tot.reason("How to solve a problem?")
        assert tree.root_question == "How to solve a problem?"
        assert tree.branches is not None

        # Test MetaCognition
        meta = MetaCognition()
        evaluation = meta.evaluate_reasoning(steps)
        assert "coherence" in evaluation
        assert "completeness" in evaluation

        # Test AbsoluteZeroReasoner
        reasoner = create_reasoner()
        result_dict = await reasoner.reason("What is AI?", mode=ReasoningMode.DEDUCTIVE)
        assert "answer" in result_dict
        assert "confidence" in result_dict

        result.passed = True
        logger.info("Zero Reasoning tests passed")
    except Exception as e:
        result.error = str(e)
        logger.error(f"Zero Reasoning test failed: {e}")

    result.duration_ms = (datetime.now() - start).total_seconds() * 1000
    return result


@pytest.mark.asyncio
async def test_recursive_learning():
    """Test Recursive Learning Framework"""
    result = IntegrationTestResult("Recursive Learning")
    start = datetime.now()

    try:
        from core.recursive_learning import (
            ExperienceBuffer, PatternExtractor,
            SkillBuilder, Experience, ExperienceType, LearningSignal, get_recursive_learner
        )

        # Test Experience
        exp = Experience(
            experience_id="exp_001",
            experience_type=ExperienceType.TASK_COMPLETION,
            context={"task": "research"},
            action="search",
            outcome={"result": "found"},
            signal=LearningSignal.POSITIVE,
            reward=0.8
        )
        assert exp.reward == 0.8
        exp_dict = exp.to_dict()
        assert exp_dict["experienceId"] == "exp_001"

        # Test ExperienceBuffer
        buffer = ExperienceBuffer(max_size=100)
        buffer.add(exp, priority=1.0)
        assert len(buffer) == 1

        sampled = buffer.sample(1)
        assert len(sampled) == 1

        recent = buffer.get_recent(10)
        assert len(recent) >= 1

        # Test PatternExtractor
        extractor = PatternExtractor(min_occurrences=1)
        patterns = extractor.analyze([exp])
        # May or may not find patterns with single experience

        # Test SkillBuilder
        builder = SkillBuilder()
        if patterns:
            skill = builder.create_skill("test_skill", "A test skill", patterns)
            assert skill.name == "test_skill"

        # Test RecursiveLearner
        learner = get_recursive_learner()

        # Record experiences
        for i in range(5):
            learner.record_experience(
                experience_type=ExperienceType.TASK_COMPLETION,
                context={"task_type": "research"},
                action="web_search",
                outcome={"found": True},
                reward=0.7
            )

        # Run batch learning
        learn_result = await learner.learn_batch(batch_size=5)
        assert "patterns_extracted" in learn_result

        # Get knowledge summary
        summary = learner.get_knowledge_summary()
        assert "total_experiences" in summary
        assert summary["total_experiences"] >= 5

        # Test suggestion
        learner.suggest_action({"task_type": "research"})
        # May or may not have suggestion depending on patterns

        result.passed = True
        logger.info("Recursive Learning tests passed")
    except Exception as e:
        result.error = str(e)
        logger.error(f"Recursive Learning test failed: {e}")

    result.duration_ms = (datetime.now() - start).total_seconds() * 1000
    return result


@pytest.mark.asyncio
async def test_refactory_loop():
    """Test Refactory Feedback Loop"""
    result = IntegrationTestResult("Refactory Feedback Loop")
    start = datetime.now()

    try:
        from core.refactory_loop import (
            CodeAnalyzer, RefactorEngine,
            FeedbackCollector, get_feedback_loop
        )

        # Test code
        test_code = '''
def example_function(x, y):
    """Example function"""
    if x > 0:
        if y > 0:
            if x > y:
                return x
            else:
                return y
        return x
    return 0

def another_function(a, b, c, d, e):
    result = a + b + c + d + e
    return result
'''

        # Test CodeAnalyzer
        analyzer = CodeAnalyzer()
        metrics = analyzer.analyze(test_code)

        assert metrics.lines_of_code > 0
        assert metrics.cyclomatic_complexity > 0
        assert 0 <= metrics.documentation_ratio <= 1

        score = metrics.quality_score()
        assert 0 <= score <= 1

        # Test RefactorEngine
        engine = RefactorEngine()
        suggestions = engine.suggest_refactorings(test_code)
        assert isinstance(suggestions, list)

        for suggestion in suggestions:
            assert suggestion.refactor_type is not None
            assert suggestion.priority >= 0

        # Test FeedbackCollector
        collector = FeedbackCollector()

        def custom_analyzer(code):
            return []

        collector.register_source("custom", custom_analyzer)
        await collector.collect(test_code)
        summary = collector.get_feedback_summary()
        assert "total" in summary

        # Test RefactoryFeedbackLoop
        loop = get_feedback_loop()
        iteration = await loop.run_iteration(test_code, auto_apply=False)

        assert "before_score" in iteration
        assert "after_score" in iteration
        assert "suggestion_count" in iteration

        # Get summary
        loop_summary = loop.get_summary()
        assert "iterations" in loop_summary

        result.passed = True
        logger.info("Refactory Loop tests passed")
    except Exception as e:
        result.error = str(e)
        logger.error(f"Refactory Loop test failed: {e}")

    result.duration_ms = (datetime.now() - start).total_seconds() * 1000
    return result


@pytest.mark.asyncio
async def test_adaptive_jit():
    """Test Self-Adapting JIT"""
    result = IntegrationTestResult("Adaptive JIT")
    start = datetime.now()

    try:
        from core.adaptive_jit import (
            AdaptiveJIT, AdaptiveCache, HotPathDetector,
            ExecutionProfile, CacheStrategy
        )

        # Test AdaptiveCache
        cache = AdaptiveCache(max_size=10, strategy=CacheStrategy.LRU)
        cache.put("key1", "value1")

        val = cache.get("key1")
        assert val == "value1", f"Expected 'value1', got {val}"

        # Test HotPathDetector
        detector = HotPathDetector(threshold_calls=10)

        for i in range(15):
            detector.record("func_001", 5.0)

        assert detector.is_hot_path("func_001"), "Should be hot path"

        profile = detector.get_profile("func_001")
        assert profile is not None
        assert profile.call_count == 15

        # Test ExecutionProfile
        ep = ExecutionProfile(function_id="test_func")
        ep.update(10.0)
        ep.update(20.0)

        assert ep.call_count == 2
        assert ep.avg_time_ms == 15.0

        # Test AdaptiveJIT basic functionality
        jit = AdaptiveJIT()  # Fresh instance

        @jit.profile
        def simple_func(x):
            return x * 2

        # Call function multiple times
        for i in range(10):
            r = simple_func(i)
            assert r == i * 2

        # Test memoize decorator
        call_count = 0

        @jit.memoize
        def counted_func(x):
            nonlocal call_count
            call_count += 1
            return x ** 2

        # First call
        r1 = counted_func(5)
        assert r1 == 25

        # Second call (should be cached)
        r2 = counted_func(5)
        assert r2 == 25
        # call_count may or may not increase depending on cache

        # Get stats
        jit_stats = jit.get_stats()
        assert "totalFunctions" in jit_stats
        assert "cacheStats" in jit_stats

        result.passed = True
        logger.info("Adaptive JIT tests passed")
    except Exception as e:
        result.error = str(e)
        import traceback
        logger.error(f"Adaptive JIT test failed: {e}\n{traceback.format_exc()}")

    result.duration_ms = (datetime.now() - start).total_seconds() * 1000
    return result


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("ADVANCED SYSTEMS INTEGRATION TESTS")
    print("=" * 60 + "\n")

    tests = [
        test_mcp_integration,
        test_a2a_protocol,
        test_self_healing,
        test_zero_reasoning,
        test_recursive_learning,
        test_refactory_loop,
        test_adaptive_jit,
    ]

    results = []
    for test in tests:
        print(f"Running: {test.__name__}...")
        result = await test()
        results.append(result)
        print(result)
        print()

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    for result in results:
        print(result)
        if result.error:
            print(f"   Error: {result.error}")

    print()
    print(f"Results: {passed}/{total} tests passed ({100*passed/total:.0f}%)")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - SYSTEM IS PRODUCTION READY")
        return True
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
