# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📋 Project Overview

**ASTRO** is a production-grade autonomous agent ecosystem that coordinates specialized AI agents to handle complex workflows. It supports multiple LLM providers (OpenAI, Ollama, OpenRouter) and includes enterprise-grade features like self-healing, A2A protocol communication, and structured reasoning engines.

**Key Characteristics:**
- Multi-agent system with 8+ specialized agents
- Python 3.10+ with async/await throughout
- Desktop GUI (TkCustom) and CLI interfaces
- 166+ test cases with comprehensive coverage
- Docker-enforced code sandbox for security
- Kubernetes-ready health probes and Prometheus metrics
- Production-hardened with detailed logging

## 🚀 Essential Commands

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (pinned versions for supply chain security)
pip install -r requirements.txt

# Load environment variables
cp .env.example .env  # (or configure via GUI Settings)
```

### Running ASTRO
```bash
# GUI (Recommended - modern dark-themed interface)
python src/gui_app.py

# CLI (Interactive mode)
python src/main.py --interactive

# CLI (Non-interactive with command)
python src/main.py "Your task description"
```

### Testing & Quality
```bash
# Run all tests (166 total)
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_security.py -v          # Security tests
python -m pytest tests/test_advanced_systems.py -v  # Enterprise systems
python -m pytest tests/test_integration.py -v       # Integration tests
python -m pytest tests/test_error_paths.py -v       # Error handling

# Run single test
python -m pytest tests/test_security.py::test_path_validation -v

# Health check
python health_check.py
```

### Linting & Code Quality
```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/
pylint src/ tests/

# Type checking
mypy src/
```

## 🏗️ Architecture & Module Organization

### Core Layer: `src/core/`
The brain of the ecosystem - manages task orchestration, agent coordination, and advanced systems.

**Key Files:**
- **engine.py** (38KB) - `AgentEngine` coordinates all agents, manages workflows, handles task execution with recovery
- **nl_interface.py** - Natural Language Interface converts user requests into structured tasks
- **agent_registry.py** - Registry for agent discovery and capability matching
- **database.py** (43KB) - SQLAlchemy-based persistence for workflows, tasks, experiences, metrics
- **task_queue.py** - Priority-based task queue with workflow support

**Advanced Systems** (Enterprise features):
- **self_healing.py** - Circuit breaker pattern, health monitoring, automatic recovery
- **a2a_protocol.py** - Agent-to-Agent communication protocol (async message bus)
- **mcp_integration.py** - Model Context Protocol support for tool integration
- **zero_reasoning.py** - Chain/Tree of Thought reasoning for complex problems
- **recursive_learning.py** - Experience replay and pattern-based learning from outcomes
- **refactory_loop.py** - Automated code quality improvement cycles
- **adaptive_jit.py** - Hot-path detection and intelligent memoization

### Agents Layer: `src/agents/`
Specialized AI workers, each inheriting from `BaseAgent`.

**Agent Implementations:**
- **base_agent.py** - Base class with timeout handling, state management, task history
- **code_agent.py** - Generates and executes code with Docker sandbox enforcement
- **research_agent.py** - Web search via DuckDuckGo, article scraping, summarization
- **filesystem_agent.py** - File CRUD operations with path validation and extension whitelist
- **git_agent.py** - Git operations (clone, commit, push, status)
- **test_agent.py** - Test execution (pytest, npm test, etc.)
- **analysis_agent.py** - Static analysis (pylint, eslint)
- **knowledge_agent.py** - Memory and context persistence

**Agent Execution Flow:**
```
User Request → NL Interface → AgentEngine (task queue) → Best Agent(s)
                                ↓
                        Self-Healing System
                        Circuit Breaker
                        Recursive Learning
                                ↓
                        Agent executes Task
                        (Docker sandbox if code)
```

### Utilities: `src/utils/`
Common functionality across the system.

- **logger.py** / **structured_logger.py** - JSON logging with context
- **config_loader.py** - YAML-based configuration loading
- Various security validators (path, code, command)

### API & Monitoring: `src/api/` and `src/monitoring/`
- FastAPI server with WebSocket support
- Prometheus metrics export
- Health endpoints (/health/live, /health/ready, /health/startup)
- Monitoring dashboard

## ⚙️ Configuration Files

**Critical Security & Behavior Settings:**

### `config/system_config.yaml`
```yaml
system.environment: "production" | "development"
system.log_level: "INFO" | "DEBUG"
llm.provider: "openai" | "ollama" | "openrouter"
llm.model_name: "gpt-4" | "gpt-3.5-turbo" | "llama3"

# Advanced Systems - all can be disabled/configured
advanced_systems.enabled: true|false
advanced_systems.self_healing.enabled: true
advanced_systems.a2a_protocol.enabled: true
advanced_systems.mcp.enabled: true
advanced_systems.learning.enabled: true
advanced_systems.reasoning.enabled: true
```

### `config/agents.yaml`
```yaml
# Code Agent - SECURITY CRITICAL
code_agent_001:
  safe_mode: true                      # AST + regex validation
  use_docker_sandbox: true             # REQUIRED for production
  allow_local_execution: false         # Only set true in dev
  docker_image: "python:3.11-slim"
  docker_execution_timeout: 30

# Filesystem Agent
filesystem_agent_001:
  root_dir: "./workspace"              # Execution sandbox
  allowed_extensions: [.txt, .py, .md, .json, .csv, .log, .yaml]

# Research Agent
research_agent_001:
  max_search_results: 6
  max_scrape_results: 4
  preferred_domains: [arxiv.org, github.com, medium.com]
```

## 🔒 Security Model

ASTRO implements defense-in-depth for code execution:

**Layer 1: Code Analysis** → AST parsing blocks dangerous patterns (exec, eval, dangerous imports)
**Layer 2: Regex Fallback** → Catches obfuscation attempts and getattr tricks
**Layer 3: Path Validation** → os.path.commonpath prevents directory traversal
**Layer 4: Docker Sandbox** → REQUIRED - isolated container, no network, read-only FS, memory limits
**Layer 5: Extension Whitelist** → Only approved file types can be created/modified

⚠️ **Critical:** `use_docker_sandbox: false` is only acceptable in local development with trusted code. Never disable for remote/untrusted input.

## 📊 Testing Strategy

### Test Organization
- **test_security.py** - Path validation, code AST blocking, command injection prevention
- **test_security_comprehensive.py** - Detailed security edge cases
- **test_advanced_systems.py** - Self-healing, A2A protocol, reasoning engines, learning
- **test_integration.py** - End-to-end workflows, agent coordination
- **test_error_paths.py** - Failure scenarios, recovery, degradation
- **test_production_features.py** - Health checks, metrics, monitoring
- **test_workflows.py** - Task queue, workflow execution, priorities

### Pytest Fixtures
The codebase uses async fixtures and mocking. Key patterns:
- `pytest-asyncio` for async test support
- Fixtures for mock LLM responses and agent instances
- Database transactions rolled back per test

### Running Tests Effectively
```bash
# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test class
pytest tests/test_security.py::TestPathValidation -v

# Run tests matching pattern
pytest tests/ -k "healing" -v

# Run with detailed output
pytest tests/ -vv --tb=long
```

## 🔄 Workflow System

**Task Execution Model:**
```
Workflow (priority, deadline, max_retries)
  ├── Task 1 (dependencies: [])
  ├── Task 2 (dependencies: [Task1])
  └── Task 3 (dependencies: [Task1, Task2])
```

**Key Classes** (in `src/core/engine.py` and `src/core/task_queue.py`):
- `Workflow` - Container with priority, timeout, retry logic
- `Task` - Individual unit of work with dependencies
- `TaskQueue` - Priority queue with dependency resolution
- `WorkflowPriority` enum - HIGH, NORMAL, LOW

**Task Execution Flow:**
1. Task moves to execution queue when dependencies met
2. AgentEngine selects best agent(s) based on capabilities
3. Self-healing system provides circuit breaker protection
4. Recursive learner suggests actions based on past patterns
5. Result stored in database for future learning
6. On failure: retry logic, degradation, or escalation

## 🤝 Agent-to-Agent Communication (A2A Protocol)

Agents can discover and delegate tasks to each other:

```python
from src.core.a2a_protocol import get_a2a_coordinator, A2ATask

coordinator = get_a2a_coordinator()
task = A2ATask(task_id="001", name="research", input_data={"topic": "AI"})
capable_agent = coordinator.find_capable_agent(["research", "web_search"])
```

**Use Cases:**
- Research agent finds article → Code agent analyzes code snippets → FileSystem agent saves results
- Code agent needs to run tests → Test agent executes tests
- FileSystem agent needs to commit changes → Git agent creates commit

## 🧠 Advanced Systems Quick Reference

### Self-Healing System
Auto-recovery with circuit breakers. Monitors component health, retries failures, graceful degradation.

### Recursive Learning
Stores task outcomes in SQLite, retrieves similar scenarios, suggests actions. NOT model fine-tuning.

### Zero Reasoning (Chain/Tree of Thought)
Forces LLM to show work step-by-step. Reduces hallucination. NOT adding reasoning to base model.

### Refactory Loop
Automated code quality suggestions. Analyzes complexity, coverage, style. LLM-powered refactoring.

### Adaptive JIT
Hot-path detection and memoization. NOT bytecode compilation. Profiles and caches frequently called functions.

### MCP Integration
Connect external tools via Model Context Protocol. Multi-server support with automatic tool routing.

## 📈 Monitoring & Observability

### Health Endpoints (Kubernetes-compatible)
```bash
curl http://localhost:8000/health           # Full status
curl http://localhost:8000/health/live      # Liveness probe
curl http://localhost:8000/health/ready     # Readiness probe
curl http://localhost:8000/health/startup   # Startup probe
```

### Prometheus Metrics (`/metrics`)
```promql
# Task success rate (last 5 minutes)
sum(rate(astro_tasks_total{status="success"}[5m])) / sum(rate(astro_tasks_total[5m]))

# P95 task duration
histogram_quantile(0.95, rate(astro_task_duration_seconds_bucket[5m]))

# Active tasks and workflows
astro_active_tasks
astro_active_workflows

# Agent health (1=healthy, 0=unhealthy)
astro_agent_health{agent_id="code_agent_001"}

# LLM cost tracking
sum(astro_llm_cost_usd) by (model)
```

### Structured JSON Logging
All logs are JSON with context:
```json
{"ts":"2025-12-13T09:40:00Z","level":"INFO","logger":"AgentEngine","msg":"Task completed","agent_id":"code_001","duration_ms":1234.5,"status":"success"}
```

Logs written to `src/logs/` directory.

## 🔧 Common Development Tasks

### Adding a New Agent
1. Create file `src/agents/my_agent.py` inheriting from `BaseAgent`
2. Implement `execute()` method and declare `capabilities`
3. Register in `AgentRegistry` (or auto-discover if using naming convention)
4. Add tests in `tests/test_integration.py`
5. Update `config/agents.yaml` with settings

### Modifying Agent Behavior
- Agent-specific settings: Edit `config/agents.yaml`
- Global settings: Edit `config/system_config.yaml`
- Settings load at startup; restart needed for changes

### Debugging Agent Execution
```bash
# Enable debug logging
python src/main.py --debug  # or set log_level: "DEBUG" in config

# Watch logs in real-time
tail -f src/logs/*.log

# Check agent health
curl http://localhost:8000/health | jq '.agents'
```

### Testing Code Agent Security
Code agent validates all inputs:
- AST inspection blocks dangerous patterns
- Path validation prevents directory traversal
- Regex checks catch obfuscation attempts
- Docker sandbox isolates execution

Run security tests with: `pytest tests/test_security.py -v`

## 🚨 Production Deployment

### Pre-Deployment Checklist
```bash
# 1. Run all tests
pytest tests/ -v

# 2. Run health check
python health_check.py

# 3. Check security
pytest tests/test_security.py tests/test_security_comprehensive.py -v

# 4. Verify environment
cat .env  # Ensure API keys are set
ls config/  # Ensure config files exist
```

### Docker Deployment
```bash
# Build image with security hardening
docker build -t astro:latest .

# Run with Docker Compose (includes monitoring)
docker-compose -f docker-compose.monitoring.yml up

# Access points:
# - ASTRO API: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

### Kubernetes Deployment
Health endpoints automatically support liveness/readiness/startup probes:
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
```

## 📚 Documentation Files
- **README.md** - User-facing guide, quickstart, FAQ
- **PRODUCTION_CHECKLIST.md** - Pre-production requirements
- **docs/engineering-charter.md** - Engineering principles
- **docs/observability.md** - Monitoring and logging details
- **docs/quality-gates.md** - Testing and quality standards
- **docs/adr/** - Architecture Decision Records

## 🔑 Key Code Patterns

### Using the Engine
```python
from src.core.engine import AgentEngine, Workflow, Task, WorkflowPriority

engine = AgentEngine()
await engine.start()

workflow = Workflow(
    workflow_id="w001",
    priority=WorkflowPriority.HIGH,
    description="Research task"
)
task = Task(task_id="t001", task_type="research", input_data={"topic": "AI"})
workflow.add_task(task)

result = await engine.execute_workflow(workflow)
```

### Async Context
The entire codebase is async. Always use:
```python
async def my_function():
    result = await agent.execute(task)
    return result

# Run from sync context
asyncio.run(my_function())
```

### Error Handling
All agent methods return `TaskResult` with structured error info:
```python
result = await agent.execute(task)
if result.success:
    print(result.result_data)
else:
    print(f"Error: {result.error_message}")
    if result.retryable:
        # Retry logic
        pass
```

## ⚠️ Important Notes

1. **Docker Sandbox is NOT Optional** - Code agent requires `use_docker_sandbox: true` in production
2. **Path Validation is Strict** - FileSystem agent uses `os.path.commonpath` to prevent traversal
3. **Async Throughout** - Don't use synchronous calls; everything is async/await
4. **Configuration at Startup** - Config files loaded once at start; changes require restart
5. **Security First** - Any user input to agents goes through validation before execution
6. **Test Before Deploy** - Run full test suite before production changes
7. **Monitor in Production** - Use health endpoints and Prometheus metrics for observability
8. **Database Migrations** - SQLAlchemy handles schema; run alembic migrations if needed

## 🌐 LLM Provider Configuration

**OpenAI (Recommended for production):**
```bash
export OPENAI_API_KEY=sk-...
python src/gui_app.py  # Set model to gpt-4 or gpt-3.5-turbo
```

**Ollama (Free, local):**
```bash
ollama pull llama3
ollama serve  # In separate terminal
python src/gui_app.py  # Set provider to ollama, model to llama3
```

**OpenRouter (Many models):**
```bash
export OPENROUTER_API_KEY=...
python src/gui_app.py  # Set provider to openrouter
```

Switch providers in GUI Settings or via environment variables.
