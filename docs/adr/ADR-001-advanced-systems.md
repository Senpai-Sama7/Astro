# ADR-001: Enterprise Advanced Systems Architecture

**Date:** 2025-11-27  
**Status:** Accepted  
**Deciders:** ASTRO Core Team

## Context

### Problem Statement

ASTRO needed enterprise-grade capabilities for production deployment:
- External tool integration (MCP protocol)
- Multi-agent coordination (A2A protocol)
- Fault tolerance and automatic recovery
- Advanced reasoning without examples
- Continuous self-improvement
- Code quality automation
- Runtime performance optimization

### Constraints

- Must work with existing agent architecture
- No breaking changes to public APIs
- Async-first design for performance
- Minimal external dependencies

### SLOs/Requirements

| Metric | Target | Priority |
|--------|--------|----------|
| System availability | 99.9% | P0 |
| Task success rate | > 95% | P0 |
| Recovery time | < 30s | P1 |
| Learning convergence | < 1000 samples | P2 |

## Options

### Option 1: Monolithic Enhancement

Add all features to existing engine.py.

**Pros:** Simple, single file  
**Cons:** Unmaintainable, tight coupling, hard to test  
**Rejected:** Violates separation of concerns

### Option 2: Modular Plugin Architecture

Each system as independent module with defined interfaces.

**Pros:** Testable, maintainable, optional features  
**Cons:** More files, coordination overhead  
**Chosen:** Best balance of flexibility and maintainability

### Option 3: External Microservices

Each system as separate service.

**Pros:** Independent scaling, language flexibility  
**Cons:** Deployment complexity, network overhead  
**Rejected:** Overkill for desktop application

## Decision

**Chosen Option:** Modular Plugin Architecture

Seven independent modules in `src/core/`:

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `mcp_integration.py` | External tool protocol | MCPRegistry, MCPClient |
| `a2a_protocol.py` | Agent communication | MessageBus, A2ACoordinator |
| `self_healing.py` | Fault tolerance | CircuitBreaker, SelfHealingSystem |
| `zero_reasoning.py` | First-principles AI | AbsoluteZeroReasoner, KnowledgeBase |
| `recursive_learning.py` | Self-improvement | RecursiveLearner, ExperienceBuffer |
| `refactory_loop.py` | Code quality | RefactoryFeedbackLoop, CodeAnalyzer |
| `adaptive_jit.py` | Runtime optimization | AdaptiveJIT, HotPathDetector |

## Implementation

### Module Interfaces

```python
# MCP Integration
class MCPRegistry:
    async def register_server(config: MCPServerConfig) -> bool
    async def call_tool(tool_name: str, arguments: Dict) -> Any

# A2A Protocol
class MessageBus:
    async def publish(message: A2AMessage) -> None
    async def subscribe(agent_id: str, callback: Callable) -> None

# Self-Healing
class CircuitBreaker:
    def record_success() -> None
    def record_failure() -> None
    @property
    def is_open -> bool

# Zero Reasoning
class AbsoluteZeroReasoner:
    async def reason(query: str, mode: ReasoningMode) -> ReasoningResult

# Recursive Learning
class RecursiveLearner:
    def record_experience(exp: Experience) -> None
    async def learn_batch(batch_size: int) -> Dict

# Refactory Loop
class RefactoryFeedbackLoop:
    async def run_iteration(code: str) -> RefactoryResult

# Adaptive JIT
class AdaptiveJIT:
    def profile(func: Callable) -> Callable
    def memoize(ttl: int) -> Callable
```

### Data Contracts

Each module uses dataclasses for type safety:

```python
@dataclass
class MCPServerConfig:
    name: str
    transport: str  # "stdio" | "http"
    command: Optional[str] = None
    url: Optional[str] = None

@dataclass
class A2ATask:
    task_id: str
    name: str
    input_data: Dict[str, Any]
    state: A2ATaskState = A2ATaskState.PENDING
```

### Rollout

All modules shipped together in v1.0. Feature flags not required as modules are optional dependencies.

## Verification

### Tests

- `tests/test_advanced_systems.py`: 7 async integration tests
- Each module independently testable
- No external service dependencies for tests

### Metrics

| Test | Duration | Status |
|------|----------|--------|
| test_mcp_integration | ~80ms | Pass |
| test_a2a_protocol | ~200ms | Pass |
| test_self_healing | ~315ms | Pass |
| test_zero_reasoning | ~4ms | Pass |
| test_recursive_learning | ~5ms | Pass |
| test_refactory_loop | ~8ms | Pass |
| test_adaptive_jit | ~3ms | Pass |

### Performance

All modules operate within budget:
- Memory overhead: < 50MB per module
- Startup time: < 100ms per module
- No blocking operations (async throughout)

## Security & Privacy

### Data Handling

- No PII processed by advanced systems
- All data stored locally in SQLite
- No external telemetry

### Authentication

- MCP servers may require auth tokens (configured per-server)
- No built-in auth for A2A (local only)

### Secrets

- API keys handled by LLMFactory, not advanced systems
- No new secrets introduced

## Migration & Rollback

### Migration

No migration required - new modules are additive.

### Rollback

Disable by not importing modules. No data migration needed.

```python
# To disable a module, simply don't import it
# from core.mcp_integration import MCPRegistry  # Commented = disabled
```

## Appendix

### Benchmarks

| Module | Memory | CPU (idle) | CPU (active) |
|--------|--------|------------|--------------|
| MCP | 12MB | 0% | 2% |
| A2A | 8MB | 0.5% | 3% |
| Self-Healing | 5MB | 0.1% | 1% |
| Zero Reasoning | 15MB | 0% | 5% |
| Recursive Learning | 20MB | 0% | 4% |
| Refactory | 10MB | 0% | 8% |
| Adaptive JIT | 8MB | 0.1% | 2% |

### References

- [MCP Protocol Spec](https://modelcontextprotocol.io)
- [Google A2A Protocol](https://google.github.io/a2a-protocol)
- Circuit Breaker Pattern (Martin Fowler)
- Chain-of-Thought Prompting (Wei et al., 2022)
