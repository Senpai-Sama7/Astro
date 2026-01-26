# ASTRO

**Autonomous System for Task and Resource Orchestration**

ASTRO is an AI-powered assistant that helps you automate tasks through natural conversation. Instead of learning complex commands or interfaces, you simply tell ASTRO what you want to do in plain English, and it figures out how to accomplish it.

---

## 🚀 Quick Start (No Coding Required!)

### Step 1: Download ASTRO
Click the green **"Code"** button above, then click **"Download ZIP"**

### Step 2: Start ASTRO
- **Windows**: Double-click `start-astro.bat`
- **Mac/Linux**: Double-click `start-astro.sh`

### Step 3: Open Your Browser
Go to **http://localhost:5000**

### Step 4: Start Chatting!
Just type what you want to do in plain English:
- *"What files are in my project?"*
- *"Run my tests"*
- *"Search the web for how to make a website"*
- *"What's 20% of 85?"*

That's it! No coding, no commands, just conversation.

---

## What Can ASTRO Do?

| Just Ask... | ASTRO Will... |
|-------------|---------------|
| *"Show me my files"* | List everything in your folder |
| *"What did I change?"* | Show your recent code changes |
| *"Run my tests"* | Run your project's tests and show results |
| *"Search for React tutorials"* | Find information online |
| *"Calculate 15% tip on $45"* | Do the math for you |
| *"Remember the API key is in .env"* | Save that for later |

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOU (Human)                             │
│                    "Run my tests and show me what failed"       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Layer 1: ARIA (Translator)                    │
│              Understands what you're asking for                 │
│         Translates your request into specific actions           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Layer 2: OTIS (Guardian)                      │
│              Checks if you're allowed to do this                │
│           Assesses risk • Logs everything for audit             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Layer 3: CORE (Orchestrator)                  │
│              Picks the right tool for the job                   │
│                   Actually runs the tests                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Layer 4: C0Di3 (Watchdog)                     │
│              Watches for security threats                       │
│         Tracks vulnerabilities • Manages incidents              │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Can ASTRO Do?

ASTRO comes with built-in capabilities organized into specialized agents:

| Agent | What It Does | Example Request |
|-------|--------------|-----------------|
| **File Agent** | Read, write, and organize files | *"Show me what's in the config folder"* |
| **Git Agent** | Check code changes and status | *"What files have I changed today?"* |
| **Test Agent** | Run your test suites | *"Run the tests and tell me if anything broke"* |
| **Research Agent** | Search the web for information | *"Find documentation for React hooks"* |
| **Code Agent** | Analyze and lint code | *"Check my code for style issues"* |
| **Knowledge Agent** | Remember things for later | *"Remember that the API key is in .env"* |

### Available Tools

- **Web Search** — Find information online
- **File Operations** — Read, write, list directories
- **Git Commands** — Status, diff (safely, without shell injection)
- **Test Running** — npm test, pytest, jest, mocha
- **Code Linting** — ESLint, Pylint
- **Math Evaluation** — Calculate expressions safely
- **HTTP Requests** — Call whitelisted APIs
- **Text Processing** — Transform, encode, hash text

---

## The Four Layers Explained

### Layer 1: ARIA (The Translator)
The conversational interface that understands natural language:
- Parses what you're asking for
- Maintains conversation context
- Handles multi-turn dialogues
- Asks for clarification when needed

### Layer 2: OTIS (The Guardian)
The security layer that protects you and your system:
- **Role-Based Access Control** — Different users get different permissions
- **Risk Assessment** — Evaluates how risky each action is before allowing it
- **Audit Logging** — Keeps tamper-proof records of everything that happens
- **Approval Workflows** — High-risk actions require explicit confirmation

### Layer 3: CORE (The Orchestrator)
The orchestration engine that actually executes tasks. It maintains a registry of available tools and agents, routes your requests to the right place, and returns results.

### Layer 4: C0Di3 (The Watchdog)
Cyber threat intelligence that monitors for security issues:
- Tracks known vulnerabilities (CVEs)
- Manages security incidents
- Integrates with MITRE ATT&CK framework
- Provides threat indicators and patterns

---

## User Roles

ASTRO supports different permission levels:

| Role | Can Execute Tools | Can Register New Tools | Can View Audit Logs | Can Manage Users |
|------|-------------------|------------------------|---------------------|------------------|
| **Admin** | ✅ | ✅ | ✅ | ✅ |
| **Analyst** | ✅ | ❌ | ✅ | ❌ |
| **Red Team** | ✅ | ✅ | ❌ | ❌ |
| **Blue Team** | ✅ | ✅ | ✅ | ❌ |
| **Read Only** | ❌ | ❌ | ✅ | ❌ |
| **Guest** | ❌ | ❌ | ❌ | ❌ |

---

## Getting Started

### Prerequisites
- Node.js 18 or higher
- Python 3.11 or higher (for Python components)

### Installation

```bash
# Clone the repository
git clone https://github.com/Senpai-Sama7/Astro.git
cd Astro

# Install dependencies
npm install

# Build the project
npm run build

# Start the server
npm start
```

### Environment Variables

Create a `.env` file with:

```env
# Required for production
JWT_SECRET=your-secret-key-here
AUDIT_SIGNING_KEY=your-audit-key-here

# Optional
PORT=5000
NODE_ENV=production
PROFILE=core
WORKSPACE_DIR=/path/to/workspace
```

### Using Docker

First, ensure your `.env` file is created as described above.

```bash
# Build the image
npm run docker:build:core

# Run the container with environment variables
docker run --env-file .env -p 5000:5000 -p 8080:8080 astro:latest-core
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Health check |
| `GET /api/v1/version` | Version and feature info |
| `POST /api/v1/aria/chat` | Send a message to ARIA |
| `GET /api/v1/astro/tools` | List available tools |
| `GET /api/v1/astro/agents` | List registered agents |
| `GET /api/v1/metrics` | Prometheus-format metrics |
| `GET /api/v1/metrics/dashboard` | Visual metrics dashboard |

### Example: Chat with ARIA

```bash
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "What files are in the current directory?"}'
```

---

## Architecture

```
src/
├── aria/           # Natural language conversation engine
├── astro/          # Tool orchestration and agent registry
├── otis/           # Security gateway (RBAC, audit, risk)
├── codi3/          # Cyber threat intelligence
├── core/           # Python backend (agents, learning, database)
├── api/            # REST API server
├── services/       # Shared services (storage, logging, metrics)
├── middleware/     # Authentication middleware
├── workflows/      # Workflow automation engine
└── plugins/        # Plugin system for custom tools
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend (TypeScript) | Express, Socket.IO |
| Backend (Python) | FastAPI, asyncio |
| Database | SQLite (embedded) |
| Authentication | JWT tokens |
| Real-time | WebSocket |
| Containerization | Docker |

---

## Security Features

ASTRO was built with security as a priority:

- **No Shell Injection** — Commands use safe argument arrays, not string concatenation
- **Path Traversal Protection** — File operations are sandboxed to the workspace
- **Input Validation** — All tool inputs are validated with schemas
- **Rate Limiting** — API and WebSocket connections are rate-limited
- **Audit Trails** — All actions are logged with tamper-evident signatures
- **Secrets Management** — Sensitive keys must be provided via environment variables

---

## Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run coverage

# Run specific test suites
npm run test:security
npm run test:integration
```

Current test coverage: **186 tests** across all components.

---

## Project Status

**Version:** 1.0.0-alpha.0

This is an alpha release. The core functionality works, but:
- Some features are still being refined
- API may change before 1.0 stable release
- Not recommended for production use without thorough testing

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Douglas Mitchell** ([@Senpai-Sama7](https://github.com/Senpai-Sama7))

---

## Acknowledgments

ASTRO builds on these excellent open-source projects:
- Express.js for the web framework
- Socket.IO for real-time communication
- mathjs for safe math evaluation
- node-html-parser for safe HTML parsing
- And many others listed in package.json
