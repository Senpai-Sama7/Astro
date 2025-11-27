# ASTRO Observability Guide

**Version:** 1.0.0  
**Last Updated:** 2025-11-27

## Overview

ASTRO uses structured logging, metrics, and health checks for production observability.

## Logging

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Development details | Function entry/exit, variable values |
| INFO | Normal operations | Task started, task completed |
| WARNING | Recoverable issues | Rate limit hit, retry triggered |
| ERROR | Failures | API error, task failed |

### Log Format

All logs use Python's standard logging with structured format:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Component Loggers

| Logger Name | Component | Purpose |
|-------------|-----------|---------|
| `MainApplication` | main.py | System lifecycle |
| `AgentEngine` | engine.py | Task orchestration |
| `ResearchAgent` | research_agent.py | Web search operations |
| `CodeAgent` | code_agent.py | Code generation/execution |
| `FileSystemAgent` | filesystem_agent.py | File operations |
| `NLInterface` | nl_interface.py | Intent classification |
| `LLMFactory` | llm_factory.py | LLM client initialization |
| `MonitoringDashboard` | monitoring_dashboard.py | Metrics collection |

### Sample Log Output

```log
2025-11-27 07:00:00,123 - AgentEngine - INFO - Task task_001 assigned to research_agent_001
2025-11-27 07:00:01,456 - ResearchAgent - INFO - Performing async web search for: AI trends
2025-11-27 07:00:03,789 - ResearchAgent - INFO - Found 5 search results
2025-11-27 07:00:05,012 - AgentEngine - INFO - Task task_001 completed successfully
```

## Metrics

### Available Metrics

#### Task Metrics

```python
# Counters
tasks_submitted_total     # Total tasks submitted
tasks_completed_total     # Total tasks completed
tasks_failed_total        # Total tasks failed

# Gauges
tasks_pending             # Current pending tasks
tasks_active              # Current active tasks
agents_active             # Current active agents

# Histograms
task_duration_seconds     # Task execution duration
```

#### Agent Metrics

```python
# Per-agent counters
agent_tasks_executed_total{agent_id}
agent_tasks_succeeded_total{agent_id}
agent_tasks_failed_total{agent_id}

# Per-agent gauges
agent_performance_score{agent_id}  # 0.0 - 1.0
agent_cpu_usage{agent_id}          # Percentage
agent_memory_usage{agent_id}       # Bytes
```

#### LLM Metrics

```python
# Counters
llm_requests_total{provider, model}
llm_errors_total{provider, error_type}

# Histograms
llm_latency_seconds{provider, model}
llm_tokens_used{provider, model, direction}  # input/output
```

### Metrics Access

Via MonitoringDashboard:

```python
from monitoring.monitoring_dashboard import MonitoringDashboard

dashboard = MonitoringDashboard()
system_health = dashboard.get_system_health()
agent_perf = dashboard.get_agent_performance("research_agent_001")
```

## Health Checks

### Comprehensive Health Check

Run `health_check.py` for full system verification:

```bash
./venv/bin/python health_check.py
```

#### Check Components

| Check | Type | Description |
|-------|------|-------------|
| Network | Optional | Internet connectivity via DuckDuckGo |
| Database | Required | SQLite file exists with required tables |
| Configs | Required | YAML files parse correctly |
| Pytest | Required | All integration tests pass |
| GUI | Required | GUI modules import successfully |
| Ollama | Optional | LLM server running with models |
| LLM E2E | Optional | Actual LLM response test |
| Web Search | Optional | DuckDuckGo search returns results |

#### Health Check Output

```
==================================================
ASTRO Comprehensive Health Check
==================================================

== Checking network connectivity ==
  ✓ Network connectivity OK

== Checking database ==
  ✓ Database OK (5 tables: agents, metrics, sqlite_sequence, tasks, workflows)

== Checking configuration files ==
  ✓ config/system_config.yaml valid
  ✓ config/agents.yaml valid

== Running advanced systems tests ==
  ✓ 7 passed in 0.65s

== Checking GUI imports ==
  ✓ GUI modules OK (10 tutorial steps, 17 colors)

== Checking Ollama LLM server ==
  ✓ Ollama running with 7 model(s)

== Running end-to-end LLM test ==
  ✓ LLM responded: 'OK'

== Testing web search ==
  ✓ Web search OK (2 results)

==================================================
SUMMARY
==================================================
  [✓] database (required)
  [✓] configs (required)
  [✓] pytest (required)
  [✓] gui (required)
  [✓] network (optional)
  [✓] ollama (optional)
  [✓] llm_e2e (optional)
  [✓] web_search (optional)

✅ HEALTH CHECK PASSED - 4/4 optional checks OK
   System is production ready!
```

## Alerting

### Alert Thresholds

| Condition | Severity | Action |
|-----------|----------|--------|
| Health check fails | Critical | Page on-call |
| Task failure rate > 10% | High | Notify team |
| LLM latency > 10s | Medium | Log warning |
| Memory > 1GB | Medium | Log warning |
| Disk space < 10% | High | Notify team |

### Alert Integration

Health check exit codes:
- `0`: All required checks pass
- `1`: One or more required checks fail

For monitoring systems:

```bash
# Prometheus blackbox exporter
./venv/bin/python health_check.py || echo "astro_health_check_failed 1"

# Simple cron alert
*/5 * * * * ./venv/bin/python /path/to/health_check.py || mail -s "ASTRO Alert" team@example.com
```

## Debugging

### Enable Debug Logging

```bash
# CLI
./venv/bin/python src/main.py --debug --interactive

# Or set environment variable
export ASTRO_LOG_LEVEL=DEBUG
./venv/bin/python src/main.py --interactive
```

### Common Debug Scenarios

#### LLM Connection Issues

```python
# Check LLM factory
from core.llm_factory import LLMFactory
client = LLMFactory.create_client("ollama")
print(f"Client type: {type(client)}")
```

#### Agent Task Failures

```python
# Enable detailed agent logging
import logging
logging.getLogger("ResearchAgent").setLevel(logging.DEBUG)
logging.getLogger("CodeAgent").setLevel(logging.DEBUG)
```

#### Database Issues

```bash
# Check database directly
sqlite3 ecosystem.db ".schema"
sqlite3 ecosystem.db "SELECT * FROM agents LIMIT 5"
```

## Dashboard Templates

### Grafana Dashboard (Future)

```json
{
  "title": "ASTRO Overview",
  "panels": [
    {"type": "stat", "title": "Active Tasks", "target": "tasks_active"},
    {"type": "graph", "title": "Task Duration", "target": "task_duration_seconds"},
    {"type": "stat", "title": "Error Rate", "target": "tasks_failed_total / tasks_submitted_total"}
  ]
}
```

### CLI Dashboard

```bash
# Watch system status
watch -n 5 './venv/bin/python -c "
from monitoring.monitoring_dashboard import MonitoringDashboard
d = MonitoringDashboard()
h = d.get_system_health()
print(f\"Health: {h[\"health_score\"]:.2f} ({h[\"status\"]})\")"'
```
