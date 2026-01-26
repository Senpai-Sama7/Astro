# ARIA - Your AI Assistant

[![CI/CD](https://github.com/Senpai-Sama7/Astro/actions/workflows/ci.yml/badge.svg)](https://github.com/Senpai-Sama7/Astro/actions)
[![Tests](https://img.shields.io/badge/tests-186%20passing-brightgreen.svg)](./tests)

**Just chat. No commands to memorize.**

ARIA is a conversational AI assistant that understands natural language. Ask it anything - calculate numbers, search the web, manage files, run workflows, or chat with AI models.

---

## Quick Start

```bash
git clone https://github.com/Senpai-Sama7/Astro.git
cd Astro && npm install
cp .env.example .env
npm run build && npm start
```

Open http://localhost:5000 and start chatting!

---

## Talk to ARIA

Just type what you need:

| You say... | ARIA does... |
|------------|--------------|
| "what's 42 times 17?" | Calculates: **714** |
| "search for TypeScript tutorials" | Searches the web |
| "read file package.json" | Shows file contents |
| "git status" | Shows repo status |
| "how's the system doing?" | Shows metrics |
| "show my workflows" | Lists your workflows |
| "run workflow daily-check" | Executes workflow |
| "ask Claude to explain recursion" | Chats with Claude |
| "help" | Shows what ARIA can do |

---

## Features

**🧮 Math** - "calculate 100 / 4", "what's 2^10?"

**🌐 Web** - "fetch https://api.example.com", "search for React hooks"

**📁 Files** - "read config.json", "list directory", "write to notes.txt"

**📊 Git** - "git status", "git diff"

**🔄 Workflows** - Create and run multi-step automations

**🤖 AI Chat** - Talk to GPT, Claude, or local models

**📈 Metrics** - Real-time system stats

---

## LLM Support

Add API keys to `.env` for AI chat:

```bash
OPENAI_API_KEY=sk-...      # GPT-4, GPT-4o
ANTHROPIC_API_KEY=sk-ant-... # Claude 3.5
# Or use local Ollama (no key needed)
```

Then just ask:
- "ask GPT to write a haiku"
- "use Claude to explain quantum computing"
- "chat with llama about Python"

---

## Workflows

Create automations that chain tools together:

```
You: "show workflows"
ARIA: 📋 Your workflows:
      • daily-check: Runs git status and lists files

You: "run workflow daily-check"
ARIA: ✅ Workflow completed!
      Results: { step1: {...}, step2: {...} }
```

---

## Plugins

Add custom tools by dropping folders in `plugins/`:

```
plugins/
└── my-plugin/
    ├── manifest.json
    └── index.js
```

ARIA automatically loads them on startup.

---

## API

Everything goes through one endpoint:

```bash
# Get a token
curl -X POST http://localhost:5000/api/v1/auth/dev-token \
  -H "Content-Type: application/json" \
  -d '{"userId": "me", "role": "admin"}'

# Chat with ARIA
curl -X POST http://localhost:5000/api/v1/aria/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "...", "message": "what can you do?"}'
```

---

## Architecture

```
┌─────────────────────────────────────────┐
│              ARIA (Layer D)             │
│     Natural Language Understanding      │
├─────────────────────────────────────────┤
│  ASTRO (A)  │  OTIS (B)  │  C0Di3 (C)  │
│   Tools &   │  Security  │   Threat    │
│   Agents    │   & RBAC   │   Intel     │
└─────────────────────────────────────────┘
```

- **ARIA**: Understands what you want, routes to the right tool
- **ASTRO**: Executes tools (18 built-in + plugins)
- **OTIS**: Security, permissions, risk scoring
- **C0Di3**: Threat detection, incident tracking

---

## Development

```bash
npm run dev      # Dev server
npm test         # Run tests
npm run lint     # Lint code
```

---

## License

MIT
