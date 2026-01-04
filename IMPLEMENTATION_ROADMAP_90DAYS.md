# Ultimate System: 90-Day Implementation Roadmap

**Start Date**: January 6, 2026 (Monday)  
**End Date**: April 5, 2026 (Sunday)  
**Status**: READY TO EXECUTE  

---

## Executive Summary

This roadmap details the **week-by-week execution plan** to build the Ultimate System—a unified 3-layer AI orchestration platform combining ASTRO (Layer A), OTIS (Layer B), and C0Di3 (Layer C).

**Key Constraint**: "*Real* is better than *perfect*. Ship v1 in 12 weeks, iterate in v2."

---

## PHASE 1: Foundation (Weeks 1-2)

### Objectives
- Set up platform repository & CI/CD pipeline
- Establish development environment
- Create base architecture scaffolding
- Get Layer A (ASTRO orchestration) running

### Week 1: Setup & Architecture

**Monday-Tuesday (Days 1-2): Repository & Tooling**

- [ ] Create `ultimate-system` repository (fork from ASTRO)
  - Keep ASTRO as git subtree (`git/astro/`)
  - Create `src/layers/` directory structure
  - Setup TypeScript config for multi-profile builds
- [ ] Setup CI/CD pipeline
  - GitHub Actions: `test.yml` (unit + integration)
  - GitHub Actions: `build.yml` (Docker images)
  - GitHub Actions: `deploy.yml` (staging K8s)
  - Add pre-commit hooks (linting, tests)
- [ ] Configure Docker multi-stage builds
  - `Dockerfile.core`: lightweight consumer image
  - `Dockerfile.cyber`: full-featured enterprise image
  - `.dockerignore`: optimize layer caching
- [ ] Setup Helm charts skeleton
  - `helm/ultimate-system/Chart.yaml`
  - `helm/values-core.yaml` (consumer defaults)
  - `helm/values-cyber.yaml` (enterprise defaults)

**Wednesday-Thursday (Days 3-4): Architecture Documentation**

- [ ] Create `/docs` structure
  - `ARCHITECTURE.md` (system design)
  - `API.md` (REST endpoints)
  - `SECURITY.md` (threat model + controls)
  - `DEVELOPMENT.md` (contributing guide)
- [ ] Design Layer A integration points
  - Define `OrchestrationRequest` interface
  - Define `SecurityGatewayDecision` interface
  - Design event schema for inter-layer communication
- [ ] Document data models
  - User/Session schema
  - Tool execution schema
  - Audit event schema
  - Memory/Knowledge base schema

**Friday (Day 5): Team Sync & Course Correction**

- [ ] Review PRs (must pass CI)
- [ ] Architecture review with security team
- [ ] Adjust timeline if needed
- [ ] Weekly retrospective

**Deliverables**:
- ✅ GitHub repo with CI/CD
- ✅ Helm charts skeleton
- ✅ Documentation structure
- ✅ Interface definitions finalized

---

### Week 2: Layer A (ASTRO) Integration

**Monday-Wednesday (Days 6-8): ASTRO Core Port**

- [ ] Port ASTRO's agent engine to `src/layers/orchestration/`
  - Copy `GemmaAgent` class
  - Copy event bus system
  - Copy agent pool (SecOps, RedTeam, BlueTeam, GeneralAssistant)
  - Copy tool registry
- [ ] Create orchestration layer facade
  - `OrchestrationEngine` class wrapping ASTRO
  - Standardize request/response interfaces
  - Add request ID tracing
  - Implement timeout & cancellation
- [ ] Setup in-memory event bus
  - Use Node.js `EventEmitter`
  - Add logging for all events
  - Add event filtering/subscription

**Thursday-Friday (Days 9-10): Testing & Integration**

- [ ] Unit tests for orchestration layer
  - 80% code coverage
  - Focus: agent routing, event emission
- [ ] Integration test: ASTRO + dummy Security Gateway
  - End-to-end request flow
  - Verify event emission
  - Check error handling
- [ ] Smoke test: Core profile Docker build
  - Image builds successfully
  - Starts without errors
  - Health check passes

**Deliverables**:
- ✅ ASTRO core ported & integrated
- ✅ Tests passing (80%+ coverage)
- ✅ Docker core image builds
- ✅ Documentation updated

---

## PHASE 2: Security Hardening (Weeks 3-6)

### Objectives
- Implement Layer B (OTIS controls)
- Add RBAC, risk evaluation, approval gates
- Implement audit logging
- Harden tool execution sandbox

### Week 3: RBAC & Authentication

**Monday-Tuesday (Days 11-12): User & Session Management**

- [ ] Implement `UserService`
  - User creation with Argon2id hashing (not custom PBKDF2!)
  - Session management (JWT + refresh tokens)
  - MFA placeholder (SMS/TOTP providers)
  - User deactivation & audit
- [ ] Add JWT middleware
  - Token validation
  - Refresh token rotation
  - Session tracking
  - Timeout handling
- [ ] Create user data model
  - SQLite schema (core profile)
  - Prisma schema (cyber profile)
  - Migrations

**Wednesday-Friday (Days 13-15): RBAC Engine**

- [ ] Implement `RBACEngine`
  - Role definitions (ADMIN, ANALYST, RED_TEAM, BLUE_TEAM, READ_ONLY, GUEST)
  - Permission matrix (tool × role)
  - Resource-level permissions (files, apis, etc.)
  - Dynamic permission loading
- [ ] Add permission checking
  - Middleware for route protection
  - Attribute-based access (if target == localhost then allow)
  - Permission inheritance (RED_TEAM ⊂ operations)
- [ ] Tests
  - 80% coverage for RBAC
  - Test matrix for each role
  - Permission denial scenarios

**Deliverables**:
- ✅ User service fully functional
- ✅ JWT auth working (all roles)
- ✅ RBAC engine enforcing rules
- ✅ Unit tests 80%+

---

### Week 4: Risk Evaluation & Approval Gates

**Monday-Wednesday (Days 16-18): CVaR-based Risk Scoring**

- [ ] Implement `RiskEvaluator`
  - Base risk from tool classification (LOW/MEDIUM/HIGH/CRITICAL)
  - Time-based factors (odd hours increase risk)
  - User history (rolling average of past risk scores)
  - Target specificity (localhost vs. remote)
  - Scheduled vs. manual execution
- [ ] Risk scoring algorithm
  - Weighted formula: tool_risk(40%) + time_risk(15%) + history_risk(20%) + context_risk(25%)
  - Output: 0-1 score
  - Clamping & normalization
- [ ] Create risk thresholds
  - LOW (0-0.25) → auto-approve
  - MEDIUM (0.25-0.5) → auto-approve (log for analytics)
  - HIGH (0.5-0.75) → human approval (manager level)
  - CRITICAL (0.75-1.0) → human approval (admin level)
- [ ] Unit tests
  - Verify scoring algorithm
  - Edge case handling
  - Threshold accuracy

**Thursday-Friday (Days 19-20): Approval Gate & Escalation**

- [ ] Implement `ApprovalGate`
  - Check if approval required
  - Route to correct approval queue (auto/manager/admin/security)
  - Track approval status (pending/approved/denied)
  - Timeout (auto-deny after 24h)
- [ ] Notification system
  - Email for approvals
  - Slack integration (optional)
  - In-app notifications
- [ ] Approval API
  - GET `/api/v1/approvals?status=pending`
  - POST `/api/v1/approvals/{id}/approve`
  - POST `/api/v1/approvals/{id}/deny`
  - Tests

**Deliverables**:
- ✅ Risk evaluation algorithm working
- ✅ Approval gate routing correctly
- ✅ Notifications configured
- ✅ Tests 80%+

---

### Week 5: Audit Logging & Compliance

**Monday-Wednesday (Days 21-23): Comprehensive Audit**

- [ ] Implement `AuditLogger`
  - Log every action: tool execution, approval, denial, escalation
  - Immutable audit trail (append-only in database)
  - Metadata capture: IP, user agent, duration, error messages
  - Structured logging (JSON format)
- [ ] Audit event schema
  - SQLite for core profile
  - PostgreSQL + Elasticsearch for cyber profile
  - Retention policies (7 days core, 365 days cyber)
  - Archival to S3 (cyber only)
- [ ] Audit APIs
  - GET `/api/v1/audit?userId={id}&action={action}&since={date}`
  - GET `/api/v1/audit/stats` (summary statistics)
  - Tests

**Thursday-Friday (Days 24-25): Compliance Framework**

- [ ] SOC 2 Type II controls
  - CC7.1: Logical access controls
  - CC7.2: Authentication
  - CC6.1: Confidentiality
  - CC6.2: Integrity
  - CC9.1: Audit logging
- [ ] ISO 27001 alignment
  - A.9.2.1: User access management
  - A.9.2.5: Access rights review
  - A.12.4.1: Logging requirements
- [ ] Add compliance checklist
  - Document controls
  - Link controls to code/configs
  - Pre-audit readiness check

**Deliverables**:
- ✅ Audit logging comprehensive
- ✅ Compliance controls documented
- ✅ Archive strategy for cyber profile
- ✅ Tests 80%+

---

### Week 6: Tool Sandbox & Hardening

**Monday-Wednesday (Days 26-28): Process Isolation**

- [ ] Implement `ToolSandbox`
  - Core profile: OS process isolation (child_process.spawn)
  - Cyber profile: Container isolation (Docker/Kubernetes)
  - Memory limits (per-tool)
  - Disk limits (per-tool)
  - Timeout enforcement
  - Signal handling (SIGTERM → graceful shutdown)
- [ ] Input validation
  - Command injection prevention
  - Path traversal prevention
  - Resource exhaustion prevention
- [ ] Output capture
  - Stdout/stderr capture
  - Parsing for errors
  - Truncation for large outputs (100MB limit)

**Thursday-Friday (Days 29-30): Security Hardening**

- [ ] Add security controls
  - No shell execution (use spawn with args array)
  - Environment variable sanitization
  - No access to system passwords/keys
  - File system ACLs (read/write restrictions)
- [ ] Cyber profile hardening
  - seccomp profiles (allow list of syscalls)
  - AppArmor/SELinux profiles
  - Network policies (ingress/egress)
  - Resource quotas (CPU, memory)
- [ ] Testing
  - Security tests (try to break out)
  - Resource limit tests
  - Timeout tests

**Deliverables**:
- ✅ Tool sandbox fully isolated
- ✅ Security hardening controls in place
- ✅ Tests 80%+ (including security tests)
- ✅ Performance benchmarks documented

---

## PHASE 3: Cyber Intelligence (Weeks 7-10)

### Objectives
- Port C0Di3 multi-layer reasoning
- Build cyber skill system
- Integrate knowledge base
- Test end-to-end workflows

### Week 7-8: C0Di3 Core Port

**[See C0Di3 implementation plan for detailed steps]**

- [ ] Port multi-layer reasoning engine
- [ ] Implement skill system
- [ ] Load knowledge base
- [ ] Tests

### Week 9-10: Knowledge Base & Integration

**[See C0Di3 integration for detailed steps]**

- [ ] Load MITRE ATT&CK data
- [ ] Load threat intelligence
- [ ] Implement vector embeddings
- [ ] End-to-end testing

**Deliverables**:
- ✅ C0Di3 fully integrated
- ✅ Cyber skills working
- ✅ Knowledge base indexed
- ✅ E2E tests passing

---

## PHASE 4: Deployment & Testing (Weeks 11-12)

### Objectives
- Build Docker images
- Create Helm charts
- Comprehensive testing (unit + integration + e2e)
- Performance benchmarking
- Documentation & launch prep

### Week 11: Docker & Kubernetes

**Monday-Wednesday (Days 71-73): Docker Images**

- [ ] Build core image
  - Multi-stage: build → runtime
  - SQLite bundled
  - ~200MB final size
  - Security scanning (trivy)
- [ ] Build cyber image
  - PostgreSQL driver included
  - Redis client included
  - ~500MB final size
  - Security scanning
- [ ] Image registry
  - Push to Docker Hub / GitHub Container Registry
  - Version tagging (semantic versioning)
  - Latest tag for current version

**Thursday-Friday (Days 74-75): Helm Charts**

- [ ] Create Helm chart for cyber profile
  - Service definitions
  - ConfigMaps for settings
  - Secrets for credentials
  - Ingress configuration
  - StatefulSet for PostgreSQL
  - Deployment for Ultimate System
- [ ] Testing
  - `helm lint` passes
  - Deploy to minikube
  - Verify services running
  - Test from outside cluster

**Deliverables**:
- ✅ Docker images published
- ✅ Helm charts functional
- ✅ Deploy to staging K8s cluster
- ✅ Security scan reports clean

---

### Week 12: Testing & Launch

**Monday-Tuesday (Days 76-77): Comprehensive Testing**

- [ ] Unit test coverage ≥80%
  - `npm run test`
  - Coverage report
  - Quality gates enforced
- [ ] Integration tests
  - API endpoints
  - Database operations
  - Audit logging
  - Risk evaluation
- [ ] End-to-end tests
  - User login → tool execution → approval → completion
  - Error scenarios
  - Timeout handling
  - Recovery from failures
- [ ] Security tests
  - RBAC violations blocked
  - Command injection attempts blocked
  - Privilege escalation impossible
  - Audit trail untampered

**Wednesday (Day 78): Performance Benchmarking**

- [ ] Benchmark core profile
  - Tool execution latency (p50, p99)
  - Memory usage at idle / 100% load
  - Concurrent task limits
  - Report metrics
- [ ] Benchmark cyber profile
  - Same metrics at 3-node scale
  - Database query performance
  - Audit logging throughput
  - Report metrics
- [ ] Compare to targets
  - Core: 150ms p50, 800ms p99 ✓
  - Cyber: 100ms p50, 300ms p99 ✓

**Thursday-Friday (Days 79-80): Documentation & Launch**

- [ ] User documentation
  - Core quick start (5 min setup)
  - Cyber deployment guide
  - API documentation (Swagger/OpenAPI)
  - FAQ & troubleshooting
- [ ] Developer documentation
  - Architecture overview
  - Adding new tools
  - Adding new agents
  - Contributing guide
- [ ] Release notes
  - v1.0.0 summary
  - Known limitations
  - Future roadmap
- [ ] Public announcement
  - Blog post
  - GitHub release
  - Social media
  - Email to stakeholders

**Deliverables**:
- ✅ All tests passing
- ✅ Performance benchmarks meet targets
- ✅ Documentation complete
- ✅ Ready for production launch

---

## Critical Path Dependencies

```
Week 1: Setup & Arch
  ↓
Week 2: Layer A (ASTRO)
  ↓
Week 3-4: Layer B (Auth & RBAC)
  ↓
Week 5-6: Layer B (Audit & Sandbox)
  ↓
Week 7-10: Layer C (C0Di3)
  ↓
Week 11-12: Deployment & Testing
  ↓
✅ v1.0.0 LAUNCH
```

## Parallel Work Streams (If Team > 2)

- **Stream A**: Architecture & Foundation (Weeks 1-2)
- **Stream B**: Layer B (Security) (Weeks 3-6) — *can start after Week 2*
- **Stream C**: Layer C (C0Di3) (Weeks 7-10) — *can start after Week 4*
- **Stream D**: DevOps & Testing (Weeks 11-12) — *can overlap from Week 6*

## Success Metrics

**Go/No-Go Criteria**:

- [ ] All tests passing (80%+ coverage)
- [ ] Security audit clean (0 critical/high findings)
- [ ] Performance benchmarks met
- [ ] Documentation complete & reviewed
- [ ] Production readiness checklist 100%
- [ ] Stakeholder sign-off obtained

**Launch Criteria**:
- Core image builds & runs successfully
- Cyber profile deploys to K8s cluster
- User can login & execute tools in < 10 seconds
- Audit trail captures all actions
- Risk evaluation working correctly
- Approval gates preventing unauthorized access

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| C0Di3 integration delays | Fallback: basic threat analysis in Layer C |
| K8s deployment complexity | Start with minikube, scale later |
| Performance miss on targets | Optimize top 20% of hot paths |
| Security findings in audit | Prioritize & fix before launch |
| Data migration issues | Test migration extensively in staging |

---

## Weekly Standup Template

**Every Friday 5 PM:**

```
## Week [N] Standup
Date: [Friday]
Attendees: [Team]

### Completed
- [ ] Deliverable 1 ✅
- [ ] Deliverable 2 ✅

### In Progress
- Deliverable 3 (85% done)

### Blockers
- None

### Next Week
- Focus on [X, Y, Z]

### Metrics
- Test coverage: 82%
- Bugs outstanding: 3 (all low priority)
- Performance latency: p50=160ms, p99=850ms
```

---

**Document Version**: 1.0  
**Last Updated**: January 3, 2026  
**Status**: READY FOR EXECUTION
