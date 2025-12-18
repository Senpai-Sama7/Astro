# ADR-000: [Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded
**Deciders:** [Names]
**Technical Story:** [Link to issue/ticket]

## Context

### Problem Statement

[Describe the problem or opportunity that requires a decision]

### Constraints

- [Constraint 1]
- [Constraint 2]

### SLOs/Requirements

| Metric | Target | Priority |
|--------|--------|----------|
| [Metric] | [Target] | [P0/P1/P2] |

### Data Sources

- [Data source 1]
- [Data source 2]

## Options

### Option 1: [Name]

**Description:** [Brief description]

**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

**Risks:**
- [Risk 1]

**Estimated Effort:** [S/M/L/XL]

### Option 2: [Name]

**Description:** [Brief description]

**Pros:**
- [Pro 1]

**Cons:**
- [Con 1]

**Risks:**
- [Risk 1]

**Estimated Effort:** [S/M/L/XL]

## Decision

**Chosen Option:** [Option N]

**Rationale:**

[Explain why this option was chosen over alternatives]

## Implementation

### Affected Modules

| Module | Change Type | Risk Level |
|--------|-------------|------------|
| [module] | New/Modified | Low/Medium/High |

### Interfaces

```python
# Key interface definitions
def new_interface(param: Type) -> ReturnType:
    """Docstring"""
    pass
```

### Data Contracts

```json
{
  "input_schema": {},
  "output_schema": {}
}
```

### Rollout Plan

1. [ ] Feature flag: `ENABLE_FEATURE_X`
2. [ ] Canary deployment (10%)
3. [ ] Gradual rollout (25% → 50% → 100%)
4. [ ] Remove feature flag

## Verification

### Tests Required

- [ ] Unit tests for [component]
- [ ] Integration tests for [flow]
- [ ] E2E tests for [scenario]

### Metrics/Observability

| Metric | Type | Threshold |
|--------|------|-----------|
| [metric] | Counter/Gauge/Histogram | [threshold] |

### Performance Targets

| Metric | Baseline | Target | Method |
|--------|----------|--------|--------|
| Latency p50 | [X]ms | [Y]ms | Load test |
| Throughput | [X]rps | [Y]rps | Load test |

## Security & Privacy

### Data Handling

- [ ] No PII processed
- [ ] Data encrypted at rest/in transit
- [ ] Retention policy defined

### Authentication/Authorization

- [ ] Auth required: [Yes/No]
- [ ] Roles affected: [List]

### Secrets Management

- [ ] New secrets required: [List]
- [ ] Rotation schedule: [Schedule]

### Compliance Notes

- [Compliance consideration 1]

## Migration & Rollback

### Migration Steps

1. [Step 1]
2. [Step 2]

### Rollback Steps

1. [Step 1]
2. [Step 2]

### Validation

```bash
# Commands to validate migration
./health_check.py
```

## Appendix

### Benchmarks

| Test | Before | After | Delta |
|------|--------|-------|-------|
| [Test] | [X] | [Y] | [Z%] |

### References

- [Link 1]
- [Link 2]

### Prior Art

- [Similar solution 1]
