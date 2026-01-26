# ARIA - Your AI Assistant

[![CI/CD](https://github.com/Senpai-Sama7/Astro/actions/workflows/ci.yml/badge.svg)](https://github.com/Senpai-Sama7/Astro/actions)
[![Tests](https://img.shields.io/badge/tests-186%20passing-brightgreen.svg)](./tests)

**Just chat. No commands to memorize.**

ARIA is a conversational AI assistant. Ask it anything - calculate numbers, search the web, manage files, run workflows, or chat with AI models.

---

## Quick Start

```bash
git clone https://github.com/Senpai-Sama7/Astro.git
cd Astro && npm install
cp .env.example .env
npm run build && npm start
```

Open http://localhost:5000 and start chatting.

---

## What You Can Say

| You say... | ARIA does... |
|------------|--------------|
| "what's 42 times 17?" | Calculates: **714** |
| "read file package.json" | Shows file contents |
| "git status" | Shows repo status |
| "how's the system doing?" | Shows metrics |
| "show my workflows" | Lists workflows |
| "run workflow daily-check" | Executes workflow |
| "ask Claude to explain recursion" | Chats with Claude |
| "help" | Shows capabilities |

---

## Features

- **Math**: "calculate 100 / 4"
- **Files**: "read config.json", "list directory"
- **Git**: "git status", "git diff"
- **Workflows**: Create and run multi-step automations
- **AI Chat**: Talk to GPT, Claude, or local Ollama models
- **Metrics**: Real-time system stats
- **Plugins**: Extend with custom tools

---

## LLM Support

Add API keys to `.env`:

```bash
OPENAI_API_KEY=sk-...      # GPT-4
ANTHROPIC_API_KEY=sk-ant-... # Claude
```

Then: "ask GPT to write a haiku" or "use Claude to explain quantum computing"

---

## Architecture

```
ARIA (Layer D) - Natural Language Interface
    ↓
ASTRO (A) + OTIS (B) + C0Di3 (C)
Tools/Agents | Security | Threat Intel
```

---

## Development

```bash
npm run dev      # Dev server
npm test         # 186 tests
npm run build    # Build
```

---

## License

MIT
