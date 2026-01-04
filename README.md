# ASTRO Ultimate System v1.0.0

[![CI/CD Pipeline](https://github.com/Senpai-Sama7/Astro/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Senpai-Sama7/Astro/actions/workflows/ci.yml)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.3+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 120+](https://img.shields.io/badge/tests-120%2B-brightgreen.svg)](./tests)
[![Coverage](https://img.shields.io/badge/coverage-%3E80%25-brightgreen.svg)](./coverage)

---

## 🎯 Four Layers of AI Orchestration

### Layer A: ASTRO (Orchestration)
Tool registry, agent management, execution engine with granular permission control.
- ✅ Tool registration (dynamic or predefined)
- ✅ Agent registry (4 predefined agents)
- ✅ Orchestration engine (single-step execution)
- ✅ HTTP API for tool execution

### Layer B: OTIS (Security)
Role-based access control, CVaR risk scoring, immutable audit logging with cryptographic signatures.
- ✅ 6-role RBAC (admin, analyst, red-team, blue-team, read-only, guest)
- ✅ CVaR-based risk scoring algorithm
- ✅ Append-only audit logging with HMAC-SHA256 signatures
- ✅ Tamper detection and integrity verification

### Layer C: C0Di3 (Cyber Intelligence)
Threat management, incident tracking, MITRE ATT&CK knowledge base, threat analytics.
- ✅ Threat registration and tracking by severity
- ✅ Incident management with timeline events
- ✅ MITRE ATT&CK framework integration
- ✅ Threat intelligence analytics and summaries

### Layer D: ARIA (Conversation)
Natural language interface for turn-by-turn control of entire system.
- ✅ Intent parsing (execute, query, help, status, approve/deny)
- ✅ Multi-turn conversation management
- ✅ Session-based context persistence
- ✅ Security-aware execution with approval workflows
- ✅ Natural language response generation

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Senpai-Sama7/Astro.git
cd Astro

# Install dependencies
npm install
```

### Development

```bash
# Start dev server
npm run dev

# Server running at http://localhost:5000
```

### Testing

```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage report
npm run coverage
```

### Production

```bash
# Build
npm run build

# Start
npm start
```

---

## 🎤 Natural Language Control

### Main Endpoint: `POST /api/v1/aria/chat`

```bash
# Example: Simple calculation
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "you",
    "userRole": "analyst",
    "message": "calculate 5 + 3"
  }'

# Response:
# {
#   "sessionId": "session_..._...",
#   "response": "✅ Calculation result: **8**",
#   "toolExecuted": true,
#   "result": {"ok": true, "data": {"result": 8}}
# }
```

### Commands

**Execute Tools:**
- `"calculate 5 + 3 * 2"`
- `"echo hello world"`
- `"fetch https://httpbin.org/get"`

**Query Information:**
- `"show agents"`
- `"show tools"`
- `"show threats"`
- `"show incidents"`

**System:**
- `"help"`
- `"status"`

**Approval:**
- `"yes"` / `"approve"`
- `"no"` / `"deny"`

---

## 📊 Raw API (Layer A)

### Execute Tool

```bash
POST /api/v1/astro/execute
{
  "agentId": "string",
  "toolName": "string",
  "input": {},
  "userId": "string"
}
```

### List Agents

```bash
GET /api/v1/astro/agents
```

### List Tools

```bash
GET /api/v1/astro/tools
```

---

## 🛡️ Security Model

### RBAC Roles

| Role | Permissions |
|------|-------------|
| **admin** | All operations |
| **blue-team** | Register tools, execute, view audit, modify risk |
| **red-team** | Register tools, execute (higher risk) |
| **analyst** | Execute tools, view audit |
| **read-only** | View audit logs only |
| **guest** | No permissions |

### Risk Scoring

- **Base**: 0.1 (all actions)
- **Red-team multiplier**: +0.3
- **Tool registration**: +0.2
- **Sensitive tools (HTTP, math)**: +0.15
- **Default threshold**: 0.5 (50%)

### Approval Workflow

When risk score >= threshold:
1. System asks for approval
2. User responds "yes" or "no"
3. Action approved/denied
4. Logged to audit trail with signature

### Audit Trail

- **Append-only**: Never modify or delete entries
- **HMAC-SHA256 signed**: Tamper-proof
- **Cryptographic verification**: Detect tampering
- **Role-based access**: Users see only authorized logs

---

## 📈 Test Coverage

**Total: 120+ tests passing**

- ASTRO Layer: 35 tests
- OTIS Layer: 20 tests
- C0Di3 Layer: 20 tests
- ARIA Layer: 20+ tests
- Integration: 25+ tests

**Coverage Target: >80%**

Run tests:
```bash
npm test
```

View coverage:
```bash
npm run coverage
```

---

## 📖 Documentation

- **[QUICKSTART.md](./QUICKSTART.md)** - Get started in 5 minutes
- **[ARIA_CONVERSATION_GUIDE.md](./ARIA_CONVERSATION_GUIDE.md)** - Natural language interface guide
- **[IMPLEMENTATION_COMPLETE.md](./IMPLEMENTATION_COMPLETE.md)** - System architecture and details

---

## 🐳 Docker Deployment

### Core Profile

```bash
# Build
npm run docker:build:core

# Run
docker run -p 5000:5000 ultimate-system:latest
```

### Test in Docker

```bash
npm run docker:test
```

---

## 📋 Project Structure

```
Astro/
├── src/
│   ├── astro/              # Layer A: Orchestration
│   │   ├── orchestrator.ts # Core orchestrator
│   │   ├── tools.ts        # Built-in tools
│   │   ├── agents.ts       # Agent definitions
│   │   └── router.ts       # HTTP API
│   ├── otis/               # Layer B: Security
│   │   └── security-gateway.ts
│   ├── codi3/              # Layer C: Intelligence
│   │   └── threat-intelligence.ts
│   ├── aria/               # Layer D: Conversation
│   │   ├── conversation-engine.ts
│   │   └── router.ts
│   ├── services/           # Shared services
│   │   └── logger.ts
│   └── index.ts            # Main entry point
├── tests/
│   ├── astro/
│   ├── otis/
│   ├── codi3/
│   ├── aria/
│   └── setup.ts
├── jest.config.js          # Jest configuration
├── tsconfig.json           # TypeScript configuration
├── package.json            # Dependencies
└── README.md               # This file
```

---

## 🔧 Development

### Lint Code

```bash
npm run lint
npm run lint:fix
```

### Format Code

```bash
npm run format
npm run format:check
```

### Type Check

```bash
npm run type-check
```

### Performance Testing

```bash
npm run perf:load
```

### Security Audit

```bash
npm run security:audit
npm run security:snyk
```

---

## 🚨 Current Status

✅ **Layer A (ASTRO)** - Production Ready
✅ **Layer B (OTIS)** - Production Ready
✅ **Layer C (C0Di3)** - Production Ready
✅ **Layer D (ARIA)** - Production Ready

**Overall: 🟢 PRODUCTION READY**

---

## 📝 License

MIT License - see [LICENSE](./LICENSE) for details

---

## 👤 Author

Douglas Mitchell <senpai-sama7@proton.me>

---

## 🙏 Contributing

Contributions welcome! Please ensure:
- All tests pass (`npm test`)
- Code is linted (`npm run lint`)
- TypeScript strict mode passes (`npm run type-check`)
- Coverage remains >80%

---

## 📞 Support

For issues, questions, or contributions, please open a GitHub issue.

---

**Built with ❤️ using TypeScript, Express, and DevOps best practices.**
