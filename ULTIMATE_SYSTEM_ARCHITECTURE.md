# Ultimate System Architecture: Consumer + Enterprise Edition

**Version**: 1.0.0  
**Date**: January 3, 2026  
**Status**: Design Phase → Implementation  
**Profiles**: `core` (consumer) | `cyber` (enterprise)  

---

## Executive Summary

The **Ultimate System** is a unified, 3-layer AI orchestration platform that combines:

1. **Layer A (Orchestration)**: ASTRO's agent engine + NL interface + workflow system
2. **Layer B (Security/Governance)**: OTIS policy gates + RBAC + risk-based approval
3. **Layer C (Cyber Intelligence)**: C0Di3 multi-layered reasoning + cyber knowledge base

Deployed as **two profiles**:
- **`core`**: Lightweight orchestrator for consumers (8GB RAM, single-node)
- **`cyber`**: Full stack for enterprises (32GB+ RAM, multi-node, hardened)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                       USER INTERFACES (Multi-modal)                  │
│         Web UI (React) | CLI | Chat API | Mobile Companion         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                    LAYER A: ORCHESTRATION (ASTRO Core)              │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Intent Router   │  │ Multi-Agent  │  │  Workflow Engine     │  │
│  │  (NL + Intent)   │  │  Coordinator │  │  (Task Sequencing)   │  │
│  └────────┬─────────┘  └──────┬───────┘  └──────────┬───────────┘  │
│           │                   │                     │              │
│  ┌────────▼───────────────────▼─────────────────────▼───────────┐  │
│  │              Event Bus (Async Communication)                  │  │
│  └────────┬─────────────────────────────────────────────────────┘  │
└───────────┼────────────────────────────────────────────────────────┘
            │
┌───────────▼────────────────────────────────────────────────────────┐
│               LAYER B: SECURITY GATEWAY (OTIS Controls)             │
│  ┌─────────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   RBAC Engine       │  │  Risk Evaluator  │  │ Approval     │  │
│  │   (Role-based)      │  │  (CVaR-based)    │  │ Gate         │  │
│  └─────────────────────┘  └──────────────────┘  └──────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Segmentation Policy | Audit Logging | Compliance Checks   │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────┬────────────────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────────┐
│            LAYER C: CYBER INTELLIGENCE (C0Di3 Pack)               │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐     │
│  │ Multi-Layer  │  │ Knowledge   │  │  Threat Reasoning    │     │
│  │ Reasoning    │  │ Base (ML)   │  │  & Decision Support  │     │
│  └──────────────┘  └─────────────┘  └──────────────────────┘     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ CyberSecOps Pack | Red/Blue Ops | Detection Engineering    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└───────┬──────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────┐
│                      TOOL SANDBOX & EXECUTION                    │
│  Safe Code Execution | Tool Registry | Input Validation        │
│  Process Isolation | Resource Limits | Timeout Control          │
└───────┬──────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────┐
│  External Tools: nmap | Metasploit | SIEM APIs | DNS/IP APIs  │
│  Local Tools: File I/O | Code Execution | Shell Commands        │
└──────────────────────────────────────────────────────────────────┘

DATA LAYER (Deployment-Dependent):
├── Core Profile:    SQLite (local) | In-Memory Cache
├── Cyber Profile:   PostgreSQL + Redis (clustered) + Vector DB
└── Logging:         Local files → ELK Stack (enterprise)
```

---

## Deployment Profiles

### Profile 1: `core` (Consumer Edition)

**Target Users**: Individual developers, small teams, hobbyists

**Stack**:
- Single-node Docker container
- SQLite local database
- In-memory event bus
- CLI + Web UI (embedded)
- No RBAC (single user)
- Sandbox: Basic (child process isolation)

**Resource Requirements**:
- Memory: 4-8 GB
- Disk: 10 GB (logs + data)
- CPU: 2+ cores

**Deploy Command**:
```bash
docker run --rm -it \
  -e PROFILE=core \
  -e LOG_LEVEL=info \
  -v ~/.ultimate-system:/data \
  ultimate-system:latest
```

**Security Level**: Medium (local execution, basic auth)

---

### Profile 2: `cyber` (Enterprise Edition)

**Target Users**: Security teams, SOCs, DevSecOps, compliance orgs

**Stack**:
- Multi-node Kubernetes cluster
- PostgreSQL (primary DB) + Redis (cache) + Weaviate (vector embeddings)
- Full RBAC + MFA + SAML/OIDC
- Advanced risk evaluation (CVaR + Bayesian updates)
- Sandbox: Hardened (seccomp + apparmor + resource quotas)
- Prometheus + Grafana + ELK Stack
- Vault for secret management

**Resource Requirements**:
- Memory: 32+ GB (split across nodes)
- Disk: 100+ GB (with log retention)
- CPU: 8+ cores distributed
- Network: Private VPC + ingress controller

**Deploy Command**:
```bash
helm install ultimate-system ./helm/ultimate-system \
  --namespace security \
  --values ./helm/values-enterprise.yaml \
  --set profile=cyber
```

**Security Level**: High (defense-in-depth, audit compliance, encryption at rest/transit)

---

## Layer-by-Layer Design

### Layer A: Orchestration (ASTRO Core)

**Components**:

1. **Intent Router**: Processes natural language or structured commands
   - Input: "Scan subnet 10.0.1.0/24 for open ports"
   - Output: Structured intent { action: 'network_scan', target: '10.0.1.0/24', tools: ['nmap'] }

2. **Multi-Agent Coordinator**: Delegates tasks to specialized agents
   - SecOps Agent (incident response)
   - Detection Engineer Agent (rule creation)
   - Red Team Agent (offensive security)
   - Blue Team Agent (defensive posture)

3. **Workflow Engine**: Chains tools and agents
   - Manage long-running tasks
   - Handle branching logic (if-then-else)
   - Support parallel execution with timeout

**Interface**:
```typescript
interface OrchestrationRequest {
  userId: string;
  sessionId: string;
  intent: string;  // Natural language
  context?: Record<string, any>;
  requestId: string;
  timeout?: number;  // ms
}

interface OrchestrationResponse {
  requestId: string;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  result?: any;
  error?: string;
  executionTime: number;  // ms
}
```

---

### Layer B: Security Gateway (OTIS Controls)

**Purpose**: Every action is authorized, evaluated for risk, and logged.

**Flow**:
1. **Authentication**: Verify user identity (JWT + refresh token)
2. **RBAC**: Check if user role has permission (fine-grained)
3. **Risk Evaluation**: Calculate CVaR of action (Bayesian inference)
4. **Approval Gate**: If risk > threshold, require human approval or escalate
5. **Audit Log**: Record decision (approved/denied/escalated) with metadata

**RBAC Model**:
```typescript
enum UserRole {
  ADMIN = 'admin',                    // All actions
  SECURITY_ANALYST = 'analyst',       // Read + safe writes
  RED_TEAM = 'red_team',              // Offensive tools (scan, exploit)
  BLUE_TEAM = 'blue_team',            // Defensive tools (detect, remediate)
  READ_ONLY = 'read_only',            // Read-only access
  GUEST = 'guest'                     // No access (policy.deny by default)
}

interface ToolPermission {
  tool: string;                       // e.g., 'nmap', 'metasploit'
  roles: UserRole[];                  // Who can run it
  maxConcurrent?: number;             // Limit parallel executions
  maxDaily?: number;                  // Rate limiting
  requiresApproval?: boolean;         // Human review needed?
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
}
```

**Risk Evaluation**:
```typescript
interface RiskContext {
  tool: string;
  target?: string;  // What are we operating on?
  action: string;   // What action?
  user: User;
  historicalRiskScore?: number;  // Rolling average
  timeOfDay?: number;            // 0-23 (detect odd hours)
  isScheduled?: boolean;
}

// CVaR calculation: "Given this action, what's the worst-case impact?"
function calculateCVaR(context: RiskContext): number {
  // Input: tool, target, user history
  // Output: Risk score 0-1
  // High score → require approval
  // Critical score → deny + alert
}
```

**Audit Schema**:
```typescript
interface AuditEvent {
  timestamp: Date;
  userId: string;
  username: string;
  sessionId: string;
  action: string;              // 'tool_executed', 'approval_denied', etc.
  resource: string;            // 'nmap', 'file_system', etc.
  decision: 'approved' | 'denied' | 'escalated';
  riskScore: number;           // 0-1
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  duration: number;            // ms
  result: 'success' | 'failure';
  errorMessage?: string;
}
```

---

### Layer C: Cyber Intelligence (C0Di3 Pack)

**Purpose**: Multi-layered reasoning for security-specific tasks.

**Skill System**:
When a user asks something security-related, ASTRO invokes C0Di3 as a "skill":

```typescript
interface CyberSkill {
  name: string;  // 'threat_analysis', 'triage_incident', 'suggest_detections'
  trigger: string[];  // Keywords that trigger this skill
  reasoning: 'multi_layer' | 'chain_of_thought' | 'tree_of_thought';
  readOnly: boolean;  // Does this change state?
  knowledgeBase: string[];  // Which KB modules to load
}

// Examples:
const threatAnalysisSkill: CyberSkill = {
  name: 'threat_analysis',
  trigger: ['analyze threat', 'threat assessment', 'threat intel'],
  reasoning: 'multi_layer',  // Use C0Di3's layers
  readOnly: true,  // Just explains
  knowledgeBase: ['attck_framework', 'threat_actors', 'indicators']
};

const incidentTriageSkill: CyberSkill = {
  name: 'triage_incident',
  trigger: ['triage incident', 'classify alert', 'assess severity'],
  reasoning: 'tree_of_thought',  // Explore decision tree
  readOnly: true,
  knowledgeBase: ['incident_response', 'severity_ratings']
};
```

**Knowledge Base Structure**:
```
data/cyber-knowledge/
├── attck-framework/          # MITRE ATT&CK data
│   ├── tactics.json
│   ├── techniques.json
│   └── relationships.json
├── threat-actors/            # Known APTs, campaigns
│   ├── actors.json
│   ├── campaigns.json
│   └── iocs.json
├── incident-response/        # IR playbooks
│   ├── playbooks.json
│   ├── escalation.json
│   └── triage_framework.json
├── detection-engineering/    # Signature / rule templates
│   ├── sigma_rules.json
│   ├── yara_rules.json
│   └── splunk_queries.json
└── vulnerability-intel/      # CVE data, exploits
    ├── cves.json
    └── exploits.json
```

**Multi-Layer Reasoning**:
1. **Layer 1 (Context)**: Understand the question in cyber domain
2. **Layer 2 (KB Retrieval)**: Fetch relevant knowledge (vector similarity)
3. **Layer 3 (Reasoning)**: Apply domain logic (decision trees, rules, ML)
4. **Layer 4 (Recommendation)**: Generate actionable output

---

## Data Flow: End-to-End Example

**User Input**: "I found suspicious logs in /var/log/auth.log. Is this a brute force attack?"

### Step 1: Intent Router (Layer A)
```
Input → "Is this a brute force attack?" + log snippet
Output → Intent { type: 'threat_analysis', domain: 'authentication', artifact: 'logs' }
```

### Step 2: Orchestration (Layer A)
```
Orchestrator recognizes → "threat_analysis" skill matches
Decides → Route to C0Di3 CyberSkill (read-only, low risk)
```

### Step 3: Security Gateway (Layer B)
```
Auth Check: User is "SECURITY_ANALYST" ✓
RBAC Check: "threat_analysis" is allowed for analyst role ✓
Risk Eval: Tool='c0di3_analysis', target='logs', action='read' → Risk Score = 0.05 (LOW)
Approval: Auto-approved (< 0.3 threshold)
Audit Log: { action: 'skill_invoked', decision: 'approved', riskScore: 0.05 }
```

### Step 4: C0Di3 Multi-Layer Reasoning (Layer C)
```
Layer 1 (Context): Detected repeated failed login attempts
Layer 2 (KB): Load MITRE ATT&CK "Initial Access" tactic, brute force technique
Layer 3 (Reasoning):
  - Check log volume: 150 failed attempts in 5 min → HIGH
  - Check source IPs: All from 203.0.113.5 → SINGLE SOURCE
  - Check time: 02:00 UTC (odd hours) → SUSPICIOUS
  - Check targets: All for 'admin' user → TARGETED
Layer 4 (Recommendation):
  - Confidence: 0.92 (HIGH)
  - Assessment: "Likely brute force attack"
  - Actions: [
      "Block IP 203.0.113.5",
      "Enable MFA for 'admin' account",
      "Review other failed login sources"
    ]
```

### Step 5: Response to User
```
{
  "assessment": "Brute force attack detected",
  "confidence": 0.92,
  "evidence": [...],
  "recommendations": [...],
  "executionTime": 245  // ms
}
```

---

## Integration Points

### ASTRO → OTIS
- Every orchestrated action passes through OTIS security gateway
- OTIS blocks/approves at Layer B before Layer C executes

### OTIS → C0Di3
- C0Di3 only executes after OTIS approval
- OTIS passes risk context to C0Di3 for decision support

### C0Di3 → Tools
- C0Di3 reasoning outputs tool recommendations
- Recommendations go back through OTIS gate for final approval

---

## Failure Handling & Fallbacks

**Scenario**: C0Di3 knowledge base offline

```typescript
if (cyberSkillUnavailable) {
  // Fallback 1: Use cached KB (30-day TTL)
  if (hasCachedKB()) return useCachedReasoning();
  
  // Fallback 2: Use basic heuristics (built-in)
  if (canUseBuiltInHeuristics()) return useBasicAnalysis();
  
  // Fallback 3: Ask for human review
  escalate({ reason: 'C0Di3 KB offline', requiresHumanReview: true });
}
```

---

## Configuration by Profile

### `core` Profile (config/profile-core.yaml)
```yaml
profile: core
mode: development  # or production

orchestration:
  maxConcurrentTasks: 5
  taskTimeout: 120000  # 2 min
  agentPool: ["SecOpsAgent"]  # Minimal set

security:
  rbac: false  # Single user
  requireApprovalAbove: 0.8  # Only critical
  auditLevel: basic

sandbox:
  isolation: process
  maxMemory: 500MB
  maxDisk: 1GB

data:
  backend: sqlite
  path: ~/.ultimate-system/data.db
  autoBackup: true

logging:
  level: info
  maxFileSize: 100MB
  maxFiles: 5
```

### `cyber` Profile (config/profile-cyber.yaml)
```yaml
profile: cyber
mode: production

orchestration:
  maxConcurrentTasks: 50
  taskTimeout: 600000  # 10 min
  agentPool: ["SecOpsAgent", "RedTeamAgent", "BlueTeamAgent", "DetectionEngineer"]

security:
  rbac: true
  mfa: true
  saml: true
  requireApprovalAbove: 0.5  # Medium+ requires review
  auditLevel: comprehensive
  encryption: aes-256-gcm

sandbox:
  isolation: container  # Docker/Kubernetes
  seccomp: strict
  apparmor: enabled
  maxMemory: 4GB
  maxDisk: 50GB
  networkPolicy: deny-by-default

data:
  backend: postgresql
  replicas: 3
  backupFrequency: hourly
  vectorDB: weaviate
  cache: redis

logging:
  level: debug
  elasticsearch: enabled
  retention: 365 days
  backup: s3://security-logs/

monitoring:
  prometheus: enabled
  grafana: enabled
  alerting: pagerduty
```

---

## Implementation Roadmap (90 Days)

**Week 1-2**: Foundation
- [ ] Create platform repo (fork from ASTRO)
- [ ] Add Layer A orchestration (ASTRO core)
- [ ] Add basic Layer B security gateway

**Week 3-6**: Security Hardening
- [ ] Implement RBAC engine
- [ ] Add risk evaluation (CVaR)
- [ ] Implement audit logging

**Week 7-10**: C0Di3 Integration
- [ ] Port C0Di3 multi-layer reasoning
- [ ] Build cyber skill system
- [ ] Integrate knowledge base

**Week 11-12**: Deployment & Testing
- [ ] Build Docker images (core + cyber)
- [ ] Create Helm charts
- [ ] Comprehensive testing (unit + integration + e2e)
- [ ] Performance benchmarking

---

## Success Metrics

**Consumer Adoption (core profile)**:
- Time-to-first-use: < 5 min
- Resource overhead: < 20% CPU at idle
- User satisfaction: > 4.5/5

**Enterprise Adoption (cyber profile)**:
- Zero security incidents (internal audit)
- Compliance: SOC 2 Type II, ISO 27001
- Audit trail completeness: 100%
- Mean approval time: < 30 sec for auto-approved

---

## Next Steps

1. **Today**: Validate architecture with stakeholders
2. **Tomorrow**: Begin Layer A implementation (branch: `feature/ultimate-system-v1`)
3. **This week**: Set up CI/CD pipeline for dual profiles
4. **This sprint**: Integrate OTIS policy engine

---

**Document Version**: 1.0  
**Last Updated**: January 3, 2026  
**Status**: Design → Implementation (Ready to merge)
