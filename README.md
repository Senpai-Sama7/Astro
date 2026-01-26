# ASTRO Ultimate System v1.0.0

[![CI/CD Pipeline](https://github.com/Senpai-Sama7/Astro/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Senpai-Sama7/Astro/actions/workflows/ci.yml)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.3+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 186](https://img.shields.io/badge/tests-186%20passing-brightgreen.svg)](./tests)
[![Coverage: 85%](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](./coverage)

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

# Optional: Add LLM API keys for multi-model support
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# Build & start
npm run build && npm start

# Server: http://localhost:5000
# WebSocket: ws://localhost:5000/ws
# Dashboard: http://localhost:5000/dashboard
# Web UI: serve ./web on port 8080
```

---

## 🔌 Plugin System

Create custom tools by adding plugins to the `plugins/` directory:

```
plugins/
└── my-plugin/
    ├── manifest.json
    └── index.js
```

**manifest.json:**
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "My custom tools",
  "tools": [
    { "name": "my_tool", "description": "Does something", "handler": "myTool" }
  ]
}
```

**index.js:**
```javascript
module.exports = {
  myTool: async (input) => {
    return { result: input.value * 2 };
  }
};
```

Tools are auto-loaded on startup and available as `my-plugin:my_tool`.

---

## 🤖 Multi-model LLM Support

Use different LLM providers via the unified API:

```bash
# List available providers
curl http://localhost:5000/api/v1/llm/providers

# Chat with default provider
curl -X POST http://localhost:5000/api/v1/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "provider": "openai",
    "model": "gpt-4o-mini"
  }'
```

Supported providers:
- **OpenAI**: GPT-4, GPT-4o, GPT-3.5 (requires `OPENAI_API_KEY`)
- **Anthropic**: Claude 3.5, Claude 3 (requires `ANTHROPIC_API_KEY`)
- **Ollama**: Local models (llama3.2, mistral, etc.)

---

## 🔄 Workflow Automation

Create and execute multi-step workflows:

```bash
# Create workflow
curl -X POST http://localhost:5000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Math Pipeline",
    "description": "Chain calculations",
    "steps": [
      { "id": "step1", "tool": "math_eval", "input": { "expression": "2+2" } },
      { "id": "step2", "tool": "echo", "input": { "message": "Result: {{step1.result}}" }, "dependsOn": ["step1"] }
    ]
  }'

# Execute workflow
curl -X POST http://localhost:5000/api/v1/workflows/wf_123/execute

# Visual builder: http://localhost:8080/workflows.html
```

---

## 📊 Metrics Dashboard

Real-time system metrics at `/dashboard`:

- Request counts by endpoint
- Tool execution stats
- Latency percentiles (avg, p95, p99)
- Memory usage
- Live latency chart

```bash
# Get metrics JSON
curl http://localhost:5000/api/v1/metrics

# Get summary
curl http://localhost:5000/api/v1/metrics/summary
```

---

## 🔌 WebSocket Support

Real-time bidirectional communication via Socket.IO:

```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000', { path: '/ws' });

// Chat with streaming
socket.emit('chat', { message: 'hello', sessionId: 'abc123' });
socket.on('chat:response', (data) => console.log(data));

// Streaming responses
socket.emit('chat:stream', { message: 'explain AI', sessionId: 'abc123' });
socket.on('stream:chunk', (chunk) => process.stdout.write(chunk));
socket.on('stream:end', () => console.log('\nDone'));

// Approval flow
socket.on('approval:required', (data) => {
  socket.emit('approve', { actionId: data.actionId });
});
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

### Specialized Agents (10)
| Agent | Tools | Purpose |
|-------|-------|---------|
| Research Agent | web_search, content_extract, http_request | Web research & summarization |
| Code Agent | echo, math_eval | Code generation & debugging |
| FileSystem Agent | read_file, write_file, list_dir | File operations (sandboxed) |
| Git Agent | git_status, git_diff | Version control |
| Test Agent | run_tests | Test execution (pytest, npm) |
| Analysis Agent | lint_code | Static analysis (eslint, pylint) |
| Knowledge Agent | save_knowledge, retrieve_knowledge | Semantic memory |
| General Assistant | echo, http_request, math_eval | General tasks |
| Math Agent | math_eval | Calculations |
| Echo Agent | echo | Testing/debugging |

### Available Tools (18)
| Tool | Description |
|------|-------------|
| `echo` | Returns input as-is (testing) |
| `http_request` | HTTP requests to whitelisted domains |
| `math_eval` | Mathematical expression evaluation |
| `web_search` | DuckDuckGo web search |
| `content_extract` | Extract text from URLs |
| `read_file` | Read files (workspace sandboxed) |
| `write_file` | Write files (workspace sandboxed) |
| `list_dir` | List directory contents |
| `git_status` | Git repository status |
| `git_diff` | Git diff output |
| `run_tests` | Execute test suites |
| `lint_code` | Run linters on code |
| `save_knowledge` | Persist key-value data |
| `retrieve_knowledge` | Retrieve stored data |
| `json_query` | Query JSON with dot notation |
| `text_transform` | upper/lower/reverse/base64 |
| `system_info` | OS/memory/CPU/disk info |
| `timestamp` | now/parse/format operations |
| `hash` | MD5/SHA1/SHA256/SHA512 |
| `uuid` | Generate UUIDs |

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

## 📊 Test Coverage

```bash
npm test          # Run all tests
npm run coverage  # Coverage report
```

| Metric | Coverage |
|--------|----------|
| Statements | 85.53% ✅ |
| Branches | 73.15% ✅ |
| Functions | 85.61% ✅ |
| Lines | 85.97% ✅ |

**Total: 186 tests passing**

---

## 🐍 Python Shells

### Vibe Shell (LLM-powered ReAct)
```bash
# Set API key
export ANTHROPIC_API_KEY=your-key  # or OPENAI_API_KEY

# Run
python vibe_shell.py
```

Features:
- Natural language → shell command bridging
- ReAct loop: Reason → Act → Observe → Answer
- Persistent sessions with history
- Tools: shell, read_file, write_file, search

### Basic Shell
```bash
python astro_shell.py
```

---

## 🐳 Docker

```bash
npm run docker:build:core
docker run -p 5000:5000 ultimate-system:latest
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment guide.

---

## 📁 Project Structure

```
Astro/
├── src/
│   ├── astro/          # Layer A: Orchestration
│   │   ├── agents.ts   # 10 specialized agents
│   │   ├── tools.ts    # 18 tool implementations
│   │   └── orchestrator.ts
│   ├── otis/           # Layer B: Security
│   ├── codi3/          # Layer C: Intelligence
│   ├── aria/           # Layer D: Conversation
│   ├── plugins/        # Plugin system
│   ├── workflows/      # Workflow automation
│   ├── services/       # WebSocket, Storage, LLM, Metrics
│   ├── middleware/     # Auth middleware
│   └── index.ts        # Entry point
├── plugins/            # Custom tool plugins
│   └── example-plugin/ # Example plugin
├── web/                # Frontend UI
│   ├── workflows.html  # Workflow builder
│   └── ...
├── tests/              # Test suites (186 tests)
├── docs/               # Documentation
│   └── DEPLOYMENT.md   # Production deployment guide
├── astro_shell.py      # Basic ReAct shell
├── vibe_shell.py       # LLM-powered ReAct shell
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

## ✅ Completed Features

- [x] 10 specialized agents
- [x] 18 tool implementations (6 new utility tools)
- [x] WebSocket support with Socket.IO
- [x] Streaming responses
- [x] Frontend-backend API integration
- [x] Test coverage at 85%+ (186 tests)
- [x] Production deployment guide
- [x] Python ReAct shells (basic + LLM-powered)
- [x] Enhanced Python TUI with status bar and agent cards
- [x] Plugin system for custom tools
- [x] Multi-model LLM support (OpenAI, Anthropic, Ollama)
- [x] Workflow automation with visual builder
- [x] Metrics dashboard with real-time charts

## 📋 Roadmap

- [x] Plugin system for custom tools
- [x] Multi-model LLM support (OpenAI, Anthropic, Ollama)
- [x] Workflow automation UI
- [x] Metrics dashboard
- [ ] Plugin marketplace
- [ ] Visual workflow designer
- [ ] Advanced analytics

---

## 📝 License

MIT License - see [LICENSE](./LICENSE)

---

**Built with TypeScript, Express, Socket.IO, and ❤️**
