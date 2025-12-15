# ADR-002: Security Audit Response - Code Execution & Terminology

**Date:** 2025-11-27
**Status:** Accepted
**Deciders:** ASTRO Core Team
**Audit Reference:** Executive Forensic Audit v1.0.0

## Context

### Problem Statement

An executive forensic audit identified three critical issues:

1. **CRITICAL SECURITY**: CodeAgent's default execution mode uses regex-based
   blocklisting which is fundamentally insecure
2. **TERMINOLOGY MISMATCH**: Module names ("Adaptive JIT", "Zero Reasoning",
   "Recursive Learning") do not accurately describe technical reality
3. **SCALABILITY**: RecursiveLearning uses JSON files which don't scale

### Audit Findings

> "The CodeAgent defaults to a 'Safe Mode' that relies on regex-based blocklisting.
> Blacklisting is fundamentally insecure for code execution. A malicious prompt
> could generate code using `getattr(__import__('os'), 'system')('rm -rf /')` or
> encoded strings to bypass checks."

## Decision

### 1. Docker Sandbox Required (CRITICAL)

**Change**: Docker sandbox is now REQUIRED by default for code execution.

```yaml
# config/agents.yaml
code_agent_001:
  use_docker_sandbox: true          # Now defaults to true
  allow_local_execution: false      # Must be explicitly enabled
```

**Behavior**:
- If Docker available → Use Docker sandbox (secure)
- If Docker unavailable AND `allow_local_execution: false` → Block execution with error
- If Docker unavailable AND `allow_local_execution: true` → Log WARNING, apply regex checks

**Security Warning Added**:
```python
# code_agent.py docstring now includes:
SECURITY WARNING:
    Regex-based blocklisting is fundamentally insecure. Attackers can bypass
    string matching via getattr(__import__('os'), 'system'), base64 encoding,
    or other dynamic execution paths. Always use Docker sandbox in production.
```

### 2. Terminology Accuracy

Module docstrings updated to accurately describe functionality:

| Module | Marketing Name | Actual Function |
|--------|---------------|-----------------|
| `adaptive_jit.py` | "JIT Optimizer" | Smart Memoization & Caching |
| `zero_reasoning.py` | "First-Principles AI" | Structured Prompt Engineering |
| `recursive_learning.py` | "Self-Improvement" | Contextual Memory (RAG-like) |

Each module now includes a `NOTE ON TERMINOLOGY` section explaining:
- What the marketing name implies
- What the code actually does
- Academic references where applicable

### 3. SQLite Persistence for Learning

**Change**: RecursiveLearning storage moved from JSON to SQLite.

**Before**:
```python
# JSON file at ~/.astro/learning/knowledge.json
with open(self.storage_path / "knowledge.json", "w") as f:
    json.dump(data, f)
```

**After**:
```python
# SQLite tables in ecosystem.db
self._db.save_learning_pattern(...)
self._db.save_learning_metadata(...)
```

**New Tables**:
```sql
CREATE TABLE learning_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_type TEXT,
    conditions TEXT,  -- JSON
    action TEXT,
    expected_outcome TEXT,
    confidence REAL,
    usage_count INTEGER,
    success_count INTEGER,
    last_used TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE learning_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,  -- JSON
    updated_at TIMESTAMP
);
```

## Consequences

### Positive

- **Security**: Code execution is now secure by default
- **Transparency**: Terminology no longer overpromises
- **Scalability**: SQLite handles millions of patterns vs JSON's practical limit

### Negative

- **Breaking Change**: Users relying on local execution must now either:
  - Install Docker
  - Explicitly enable `allow_local_execution: true` (not recommended)
- **Migration**: Existing `knowledge.json` files won't auto-migrate (manual import needed)

### Neutral

- File names kept unchanged (`adaptive_jit.py`) for backward compatibility
- Docker image download adds ~100MB on first use

## Verification

```bash
# Verify security default
python -c "from agents.code_agent import CodeAgent; c = CodeAgent('test', {}); print('use_docker:', c.use_docker, 'allow_local:', c.allow_local_execution)"
# Expected: use_docker: True (or False if Docker missing), allow_local: False

# Verify SQLite tables exist
sqlite3 ecosystem.db ".tables" | grep learning
# Expected: learning_metadata  learning_patterns

# Full health check
python health_check.py
# Expected: 8/8 checks pass
```

## References

- Original Audit: "Executive Forensic Audit: Autonomous Agent Ecosystem"
- Docker Security: https://docs.docker.com/engine/security/
- Wei et al., "Chain-of-Thought Prompting" (2022)
