# ASTRO Ultimate System v1.0.0

[![CI/CD Pipeline](https://github.com/Senpai-Sama7/Astro/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Senpai-Sama7/Astro/actions/workflows/ci.yml)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.3+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 79](https://img.shields.io/badge/tests-79%20passing-brightgreen.svg)](./tests)

---

## 🎯 Four Layers of AI Orchestration

| Layer | Name | Description | Status |
|-------|------|-------------|--------|
| A | **ASTRO** | Tool orchestration, agent management, execution engine | ✅ Active |
| B | **OTIS** | RBAC security, CVaR risk scoring, audit logging | ✅ Active |
| C | **C0Di3** | Threat management, MITRE ATT&CK, incident tracking | ✅ Active |
| D | **ARIA** | Natural language conversation interface | ✅ Active |

---

## 🖥️ Screenshots

### Homepage (Online)
![Homepage](screenshots/homepage-online.png)

### Chat Interface
![Chat](screenshots/chat-page.png)

---

## 🚀 Quick Start

```bash
# Clone & install
git clone https://github.com/Senpai-Sama7/Astro.git
cd Astro && npm install

# Create .env from example
cp .env.example .env

# Build & start
npm run build && npm start

# Server: http://localhost:5000
# Web UI: serve ./web on port 8080
```

---

## 🎤 API Endpoints

### Authentication
```bash
# Get dev token
curl -X POST http://localhost:5000/api/v1/auth/dev-token \
  -H "Content-Type: application/json" \
  -d '{"userId": "test", "role": "admin"}'
```

### Chat (Layer D - ARIA)
```bash
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"message": "help"}'
```

### Available Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/version` | GET | Version & layer status |
| `/api/v1/auth/dev-token` | POST | Issue dev JWT |
| `/api/v1/aria/chat` | POST | Chat interface |
| `/api/v1/aria/examples` | GET | Command examples |
| `/api/v1/astro/agents` | GET | List agents |
| `/api/v1/astro/tools` | GET | List tools |
| `/api/v1/astro/execute` | POST | Execute tool |

---

## 🤖 Agents & Tools

### Current Agents (Backend)
| Agent | Tools | Purpose |
|-------|-------|---------|
| General Assistant | echo, http_request, math_eval | General tasks |
| Analyst Agent | http_request, math_eval | Data analysis |
| Echo Agent | echo | Testing |
| Math Agent | math_eval | Calculations |

### Available Tools
- **echo** - Returns input as-is (testing)
- **http_request** - HTTP requests to whitelisted domains
- **math_eval** - Mathematical expression evaluation

---

## 🛡️ Security (Layer B - OTIS)

### RBAC Roles
| Role | Permissions |
|------|-------------|
| admin | All operations |
| blue-team | Register tools, execute, view audit |
| red-team | Register tools, execute (higher risk) |
| analyst | Execute tools, view audit |
| read-only | View audit logs only |
| guest | No permissions |

### Risk Scoring (CVaR)
- Actions with risk score ≥ 0.5 require approval
- Audit trail with HMAC-SHA256 signatures
- Tamper detection and integrity verification

---

## 📊 Test Status

```bash
npm test          # Run all tests
npm run coverage  # Coverage report
```

**Current:** 79 tests passing | ~52% coverage (target: 80%)

---

## 🐳 Docker

```bash
npm run docker:build:core
docker run -p 5000:5000 ultimate-system:latest
```

---

## 📁 Project Structure

```
Astro/
├── src/
│   ├── astro/          # Layer A: Orchestration
│   ├── otis/           # Layer B: Security
│   ├── codi3/          # Layer C: Intelligence
│   ├── aria/           # Layer D: Conversation
│   └── index.ts        # Entry point
├── web/                # Frontend UI
├── tests/              # Test suites
├── screenshots/        # UI screenshots
└── astro_os/           # Python TUI (experimental)
```

---

## 🔧 Development

```bash
npm run dev           # Dev server with hot reload
npm run lint          # Lint code
npm run format        # Format code
npm run type-check    # TypeScript check
```

---

## 📋 Roadmap

- [ ] Implement specialized agents (Research, Code, FileSystem, Git, Test, Analysis, Knowledge)
- [ ] Connect chat UI to backend API
- [ ] Increase test coverage to 80%
- [ ] Add WebSocket support for real-time updates
- [ ] Implement agent status API for frontend

---

## 📝 License

MIT License - see [LICENSE](./LICENSE)

---

**Built with TypeScript, Express, and ❤️**
