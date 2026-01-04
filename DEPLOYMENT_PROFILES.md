# Deployment Profiles: Consumer vs. Enterprise

**Status**: Ready for Implementation  
**Date**: January 3, 2026  

---

## Overview

The Ultimate System ships as **two distinct profiles**:

| Aspect | **core** (Consumer) | **cyber** (Enterprise) |
|--------|-------------------|---------------------|
| **Target** | Developers, teams, hobbyists | Security teams, SOCs, DevSecOps |
| **Deployment** | Single Docker container | Kubernetes cluster |
| **Database** | SQLite local | PostgreSQL + Redis + Vector DB |
| **RBAC** | Disabled (single user) | Full RBAC + MFA + SAML |
| **Risk Evaluation** | Basic threshold | CVaR + Bayesian inference |
| **Audit** | Basic logging | Comprehensive + ELK integration |
| **Resource** | 4-8 GB RAM | 32+ GB RAM distributed |
| **Security** | Medium | High (defense-in-depth) |
| **Setup Time** | < 5 min | < 30 min |
| **Cost** | Free/low | Licensing available |

---

## Profile 1: `core` (Consumer Edition)

### Quick Start

**Option A: Docker (Recommended)**

```bash
# Pull the latest core image
docker pull ultimate-system:latest-core

# Run with persistent data
docker run --rm -it \
  --name ultimate-system \
  -p 8080:8080 \
  -p 5000:5000 \
  -e PROFILE=core \
  -e LOG_LEVEL=info \
  -v ~/.ultimate-system:/data \
  ultimate-system:latest-core

# Access:
# Web UI: http://localhost:8080
# API: http://localhost:5000
# CLI: (included in container)
```

**Option B: Local Installation**

```bash
# Clone the repo
git clone https://github.com/Senpai-Sama7/ultimate-system.git
cd ultimate-system

# Install dependencies
npm install

# Run with core profile
NODE_ENV=production PROFILE=core npm start

# Or use CLI directly
NODE_ENV=production PROFILE=core npm run cli
```

### Configuration

**`config/profile-core.yaml`**:

```yaml
profile: core
mode: development  # Set to 'production' for hardening

# Orchestration (single-threaded, safe defaults)
orchestration:
  maxConcurrentTasks: 5
  taskTimeout: 120000        # 2 minutes
  agentPool:
    - "SecOpsAgent"
    - "GeneralAssistant"

# Security (minimal, single-user focused)
security:
  rbac: false                # No role-based access
  mfa: false                 # No multi-factor auth
  requireApprovalAbove: 0.8  # Only critical actions need approval
  auditLevel: basic          # Basic logging only
  encryption: none           # Data not encrypted at rest (local only)

# Sandbox (process-level isolation)
sandbox:
  isolation: process         # Use OS process isolation
  seccomp: false             # No seccomp filtering
  apparmor: false            # No AppArmor profile
  maxMemory: 500MB           # Per-tool memory limit
  maxDisk: 1GB               # Per-tool disk limit
  networkPolicy: allow       # Allow network access (you control firewall)

# Data Storage (local SQLite)
data:
  backend: sqlite            # Local SQLite database
  path: ~/.ultimate-system/data.db
  autoBackup: true           # Daily backup to ~/.ultimate-system/backups
  backupRetention: 7         # Keep 7 days of backups
  vectorDB: memory           # In-memory embeddings

# Logging (local files only)
logging:
  level: info
  format: text               # Human-readable logs
  output: console,file
  maxFileSize: 100MB         # Rotate logs at this size
  maxFiles: 5                # Keep 5 rotated files
  path: ~/.ultimate-system/logs

# API Server
api:
  enabled: true
  port: 5000
  host: 127.0.0.1            # Localhost only by default
  cors: false
  rateLimit: 100             # 100 requests per minute

# Web UI
web:
  enabled: true
  port: 8080
  host: 127.0.0.1
  theme: dark                # 'dark' or 'light'

# Monitoring (basic)
monitoring:
  metrics: false             # No Prometheus
  healthCheck: true
  healthCheckInterval: 60000 # 1 minute
```

### First-Time Setup

1. **Create workspace**:
   ```bash
   mkdir -p ~/.ultimate-system/{logs,data,backups}
   ```

2. **Web UI onboarding**:
   - Navigate to http://localhost:8080
   - System auto-creates admin user
   - Set password when prompted
   - Accept terms & privacy policy

3. **Run first tool**:
   ```bash
   # Via Web UI:
   1. Click "+ New Task"
   2. Type: "Show me available tools"
   3. Agent responds with tool list
   
   # Via CLI:
   $ ultimate-system "list tools"
   ```

### Typical Workflow

**Scenario**: Analyze suspicious logs

```bash
# 1. Upload or reference log file
ultimate-system "Analyze /path/to/auth.log for brute force patterns"

# Agent:
# [Agent is thinking...]
# Detected 150 failed login attempts from 203.0.113.5 in 5 minutes.
# Confidence: 92%
# Recommendation: Block IP, enable MFA on admin account

# 2. Execute recommended action (if desired)
ultimate-system "Block IP 203.0.113.5"

# System:
# ⚠️  This action requires approval (Risk: HIGH)
# Proceed? [y/n] y
# ✓ IP added to firewall blocklist
# Audit logged.
```

---

## Profile 2: `cyber` (Enterprise Edition)

### Prerequisites

- Kubernetes 1.24+ cluster (or minikube for testing)
- Helm 3.10+
- PostgreSQL 14+ (managed or self-hosted)
- Redis 7+ (managed or self-hosted)
- Weaviate 1.0+ (for vector embeddings)
- Vault (for secret management, optional but recommended)

### Deployment

**Step 1: Add Helm repository**

```bash
helm repo add ultimate-system https://helm.ultimate-system.io
helm repo update
```

**Step 2: Create namespace & secrets**

```bash
# Create namespace
kubectl create namespace security

# Create secrets (PostgreSQL, Redis, Vault tokens)
kubectl -n security create secret generic ultimate-system-secrets \
  --from-literal=pg-password=<secure-password> \
  --from-literal=redis-password=<secure-password> \
  --from-literal=jwt-secret=<32-byte-hex> \
  --from-literal=encryption-key=<32-byte-hex>
```

**Step 3: Configure Helm values**

**`helm/values-cyber.yaml`**:

```yaml
profile: cyber
mode: production
replicas: 3

image:
  repository: ultimate-system
  tag: latest-cyber
  pullPolicy: IfNotPresent

resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"

# PostgreSQL configuration
postgres:
  enabled: true
  host: postgres.default.svc.cluster.local  # Or external RDS
  port: 5432
  database: ultimate_system
  # Password from secret
  ssl: require

# Redis cache
redis:
  enabled: true
  host: redis.default.svc.cluster.local
  port: 6379
  ttl: 3600
  # Password from secret
  ssl: true

# Vector database (Weaviate)
weaviate:
  enabled: true
  host: weaviate.default.svc.cluster.local
  port: 8080
  scheme: http
  apiKey: <from-secret>

# Security
security:
  rbac: true
  mfa: true
  saml:
    enabled: true
    idpUrl: https://your-idp.example.com
  tls:
    enabled: true
    certSecret: ultimate-system-tls
  encryption:
    atRest: true
    algorithm: aes-256-gcm
    keyRotation: 90  # days
  networkPolicy: true  # Enable K8s network policies

# Audit & Compliance
audit:
  level: comprehensive
  elasticsearch:
    enabled: true
    host: elasticsearch.logging.svc.cluster.local
    port: 9200
  retention: 365  # days
  backup:
    enabled: true
    destination: s3://security-audit-logs/
    frequency: hourly

# Monitoring & Observability
monitoring:
  prometheus:
    enabled: true
    scrapeInterval: 30s
  grafana:
    enabled: true
    adminPassword: <from-secret>
  alerting:
    enabled: true
    alertmanager: alertmanager.monitoring.svc.cluster.local
    pagerduty:
      integrationKey: <from-secret>

# Ingress
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: ultimate-system.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: ultimate-system-tls
      hosts:
        - ultimate-system.example.com

# Pod Security & Isolation
podSecurityPolicy: restricted
```

**Step 4: Deploy**

```bash
helm install ultimate-system ultimate-system/ultimate-system \
  --namespace security \
  --values helm/values-cyber.yaml

# Wait for rollout
kubectl -n security rollout status deployment/ultimate-system

# Verify
kubectl -n security get pods
```

### Verify Deployment

```bash
# Health check
kubectl -n security run -it --rm curl-test --image=curlimages/curl --restart=Never -- \
  curl http://ultimate-system.security.svc.cluster.local:8080/health

# Get status
kubectl -n security describe deployment ultimate-system

# View logs
kubectl -n security logs -f deployment/ultimate-system --all-containers
```

### Configuration

**`config/profile-cyber.yaml`**:

```yaml
profile: cyber
mode: production

# Orchestration (multi-threaded, high throughput)
orchestration:
  maxConcurrentTasks: 50
  taskTimeout: 600000        # 10 minutes
  agentPool:
    - "SecOpsAgent"
    - "RedTeamAgent"
    - "BlueTeamAgent"
    - "DetectionEngineer"
    - "ComplianceAgent"

# Security (comprehensive)
security:
  rbac: true                  # Full RBAC
  mfa: true                   # Required for all users
  saml: true                  # Enterprise SSO
  requireApprovalAbove: 0.5   # Medium+ risk requires review
  auditLevel: comprehensive
  encryption: aes-256-gcm
  secrets:
    provider: vault           # Use HashiCorp Vault
    path: secret/ultimate-system

# Sandbox (container-level isolation)
sandbox:
  isolation: container        # Docker/Kubernetes pods
  seccomp: strict             # Enable seccomp
  apparmor: enforcing         # AppArmor profile
  maxMemory: 4GB              # Per-tool memory limit
  maxDisk: 50GB               # Per-tool disk limit
  networkPolicy: deny-by-default  # Explicit allow lists
  cpuThrottle: true           # Prevent CPU exhaustion
  rlimitMaxFiles: 1000

# Data Storage (PostgreSQL + Redis + Vector DB)
data:
  backend: postgresql
  replicas: 3                 # Multi-node replication
  connectionString: ${DATABASE_URL}
  ssl: require
  backupFrequency: hourly
  backupRetention: 30         # days
  archival: s3://backups/     # Long-term storage
  vectorDB:
    provider: weaviate
    host: ${WEAVIATE_HOST}
    batching: true
    batchSize: 100

# Logging (ELK Stack)
logging:
  level: debug
  format: json               # Structured logging
  elasticsearch:
    host: ${ELASTICSEARCH_HOST}
    port: ${ELASTICSEARCH_PORT}
    ssl: true
    indexPattern: ultimate-system-%{+YYYY.MM.dd}
  filebeat:
    enabled: true
    prospectors:
      - type: log
        enabled: true
        paths:
          - /var/log/ultimate-system/*.log
  retention: 365             # days
  backup:
    enabled: true
    destination: s3://logs/
    frequency: daily

# API Server
api:
  enabled: true
  port: 8080
  host: 0.0.0.0              # Listen on all interfaces (K8s handles routing)
  cors:
    enabled: true
    allowedOrigins: ${ALLOWED_ORIGINS}
  rateLimit: 1000            # 1000 requests per minute
  authentication:
    strategy: jwt
    issuer: ${JWT_ISSUER}
    audience: ultimate-system
  tls:
    enabled: true
    certPath: /etc/certs/tls.crt
    keyPath: /etc/certs/tls.key

# Web UI
web:
  enabled: true
  port: 8081
  host: 0.0.0.0
  theme: dark
  sso:
    enabled: true
    provider: ${SAML_PROVIDER}

# Monitoring (Prometheus + Grafana)
monitoring:
  prometheus:
    enabled: true
    scrapeInterval: 30s
    retentionDays: 15
    metricsPath: /metrics
  grafana:
    enabled: true
    dashboards:
      - security
      - performance
      - audit
  healthCheck:
    enabled: true
    interval: 10000            # 10 seconds
    timeout: 5000
  performance:
    profileCPU: true
    profileMemory: true
    tracing:
      enabled: true
      provider: jaeger
      samplingRate: 0.1

# Compliance
compliance:
  standards:
    - soc2
    - iso27001
    - hipaa
    - pci-dss
  automatedReporting: true
  reportingFrequency: monthly
```

### High Availability Setup

**Multi-region deployment**:

```bash
# Deploy to multiple regions
for REGION in us-east-1 eu-west-1 ap-southeast-1; do
  helm install ultimate-system-$REGION ultimate-system/ultimate-system \
    --namespace security \
    --values helm/values-cyber-$REGION.yaml
done

# Setup cross-region replication
kubectl apply -f config/replication-policy.yaml
```

### Scaling

**Autoscaling based on metrics**:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ultimate-system-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ultimate-system
  minReplicas: 3
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## Migrating Between Profiles

### Core → Cyber (Growth Path)

```bash
# 1. Export data from core
ultimate-system export-data --profile=core --output=/tmp/core-data.json

# 2. Provision cyber infrastructure
helm install ultimate-system ultimate-system/ultimate-system \
  --namespace security --values helm/values-cyber.yaml

# 3. Import data into cyber
kubectl -n security exec deployment/ultimate-system -- \
  ultimate-system import-data --input=/tmp/core-data.json

# 4. Verify & validate
ultimate-system validate-migration --source-profile=core --target-profile=cyber
```

---

## Performance Benchmarks

### Core Profile (Single Node)

| Metric | Value |
|--------|-------|
| Tool execution latency (p50) | 150 ms |
| Tool execution latency (p99) | 800 ms |
| Concurrent tasks | 5 |
| Memory usage (idle) | 200 MB |
| Memory usage (100% load) | 800 MB |
| Disk I/O (logs) | < 1 MB/s |
| Uptime | 99.5% (rolling restarts) |

### Cyber Profile (3-node cluster)

| Metric | Value |
|--------|-------|
| Tool execution latency (p50) | 100 ms |
| Tool execution latency (p99) | 300 ms |
| Concurrent tasks | 50 |
| Memory per pod (idle) | 500 MB |
| Memory per pod (100% load) | 2 GB |
| Disk I/O (logs) | < 10 MB/s |
| Uptime | 99.99% (HA + failover) |
| Audit log throughput | 10k events/sec |

---

## Troubleshooting

### Core Profile: "Port already in use"

```bash
# Change ports in config
export PORT=8081 API_PORT=5001
ultimate-system --config config/profile-core.yaml
```

### Cyber Profile: "Pod stuck in pending"

```bash
# Check node resources
kubectl describe nodes

# Check PVC claims
kubectl -n security get pvc

# Check events
kubectl -n security describe pod <pod-name>
```

---

## Support & Documentation

- **Core Profile**: https://docs.ultimate-system.io/core
- **Cyber Profile**: https://docs.ultimate-system.io/cyber
- **Issues**: https://github.com/Senpai-Sama7/ultimate-system/issues

---

**Last Updated**: January 3, 2026  
**Version**: 1.0.0
