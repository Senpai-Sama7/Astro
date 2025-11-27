# ASTRO Quality Gates

**Version:** 1.0.0  
**Last Updated:** 2025-11-27

## Pre-Commit Gates

All changes must pass these gates before merge.

### 1. Syntax Validation

```bash
# All Python files must compile
python -m py_compile src/**/*.py
```

**Threshold:** 0 errors

### 2. Test Suite

```bash
# Run all tests
./venv/bin/python -m pytest tests/ -v

# Required coverage (future)
# ./venv/bin/python -m pytest --cov=src --cov-fail-under=80
```

**Thresholds:**
- All tests pass: Required
- Test count: Minimum 7 (advanced systems)
- Coverage: Target 80% (not enforced yet)

### 3. Health Check

```bash
./venv/bin/python health_check.py
```

**Required Checks (must pass):**
- Database integrity
- Config validation
- Pytest suite
- GUI imports

**Optional Checks (should pass):**
- Network connectivity
- Ollama server
- LLM E2E test
- Web search

### 4. Type Checking (Future)

```bash
# When enabled
mypy src/ --ignore-missing-imports
```

**Threshold:** 0 errors (not enforced yet)

### 5. Security Scan

```bash
# Check for hardcoded secrets
grep -rn "sk-\|api_key.*=.*['\"]" src/ --include="*.py" | grep -v "getenv\|environ"
```

**Threshold:** 0 matches (excluding env var usage)

## Performance Gates

### Response Time Budgets

| Operation | P50 Target | P99 Target | Alert |
|-----------|------------|------------|-------|
| CLI startup | < 500ms | < 1s | > 2s |
| GUI startup | < 2s | < 5s | > 10s |
| LLM response (Ollama) | < 2s | < 10s | > 30s |
| Web search | < 3s | < 8s | > 15s |
| Task execution | < 5s | < 30s | > 60s |

### Memory Budgets

| Component | Target | Alert |
|-----------|--------|-------|
| Idle GUI | < 200MB | > 400MB |
| Active processing | < 500MB | > 1GB |
| Peak memory | < 1GB | > 2GB |

## CI/CD Gates

### Build Pipeline

```yaml
stages:
  - lint
  - test
  - security
  - build

lint:
  script:
    - python -m py_compile src/**/*.py
  allow_failure: false

test:
  script:
    - pip install -r requirements.txt
    - python -m pytest tests/ -v
  allow_failure: false

security:
  script:
    - pip-audit --requirement requirements.txt
  allow_failure: true  # Advisory only

build:
  script:
    - python health_check.py
  allow_failure: false
```

### Release Gates

Before any release:

1. [ ] All tests pass
2. [ ] Health check passes with 4/4 optional checks
3. [ ] No critical security advisories
4. [ ] README version updated
5. [ ] CHANGELOG updated

## Monitoring Gates

### Required Logs

Every request must log:

```python
{
    "timestamp": "ISO8601",
    "level": "INFO|WARNING|ERROR",
    "component": "agent|engine|gui",
    "action": "task_start|task_complete|error",
    "task_id": "uuid",
    "duration_ms": 123,
    "success": true
}
```

### Required Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `astro_tasks_total` | Counter | agent, status |
| `astro_task_duration_seconds` | Histogram | agent |
| `astro_llm_requests_total` | Counter | provider, model |
| `astro_errors_total` | Counter | component, error_type |

## Validation Commands

```bash
# Full validation suite
./venv/bin/python health_check.py && \
./venv/bin/python -m pytest tests/test_advanced_systems.py -v && \
echo "All gates passed"
```

## Gate Bypass Process

For emergency fixes:

1. Create issue documenting bypass
2. Get approval from 2 maintainers
3. Add `[GATE-BYPASS]` to commit message
4. Schedule follow-up to restore gate compliance
