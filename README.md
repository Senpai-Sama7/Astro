<div align="center">

# 🚀 ASTRO

### **Your AI-Powered Assistant That Actually Understands You**

[![Version](https://img.shields.io/badge/version-1.0.0--alpha.0-blue.svg)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Tests](https://img.shields.io/badge/tests-248%20passing-brightgreen.svg)]()
[![Security](https://img.shields.io/badge/security-hardened-success.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-ruff-purple.svg)]()

**No coding required. Just talk to your computer like a person.**

[📥 Download Now](#-download--install) • [🎯 Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [💬 Discord](#)

</div>

---

## 🌟 What is ASTRO?

ASTRO is like having a **smart assistant** living in your computer. Instead of memorizing complicated commands or clicking through endless menus, you simply *tell* it what you want in plain English.

### 👋 For Everyone (No Tech Skills Needed!)

| ❌ Old Way | ✅ With ASTRO |
|-----------|---------------|
| Google "how to find large files on my computer" | *"Show me files bigger than 100MB"* |
| Manually check what you changed in a document | *"What did I change today?"* |
| Learn complex terminal commands | *"Run my tests and tell me if anything broke"* |
| Copy-paste between calculator and document | *"What's 15% tip on $85.50?"* |
| Forget where you saved something | *"Find my vacation photos from last summer"* |

### 🖥️ For Developers & Power Users

ASTRO provides a **secure, auditable, AI-powered command layer** over your system with:
- Multi-layer security architecture (RBAC, audit trails, risk assessment)
- ReAct-based reasoning with LLM fallback
- Sandboxed file operations with path traversal protection
- Structured logging and Prometheus metrics
- Docker deployment ready

---

## 🎬 See It In Action

```
┌─────────────────────────────────────────────────────────────────────┐
│  💬 You: "Show me all Python files I modified today"                │
│                                                                     │
│  🤖 ASTRO:                                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ I found 3 Python files you modified today:                  │   │
│  │                                                             │   │
│  │ 📄 src/auth/login.py     - Modified 2 hours ago             │   │
│  │ 📄 tests/test_api.py     - Modified 30 minutes ago          │   │
│  │ 📄 config/settings.py    - Modified 5 minutes ago           │   │
│  │                                                             │   │
│  │ The largest change was in test_api.py (+45 lines)           │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Why Choose ASTRO?

<div align="center">

| 🛡️ **Secure by Design** | ⚡ **Lightning Fast** | 🧠 **Actually Smart** |
|--------------------------|----------------------|----------------------|
| Sandboxed operations, audit trails, no shell injection | Local-first with optional cloud AI | Understands context, learns your patterns |

| 🔒 **Private** | 🎨 **Simple** | 🔧 **Powerful** |
|---------------|----------------|----------------|
| Your data stays on your machine | No learning curve - just chat | Handles complex multi-step tasks |

</div>

---

## 🆕 What's New: ASTRO Core

ASTRO Core is a comprehensive AI agent platform with advanced capabilities:

### 🤖 Universal LLM Provider System
- **6 Providers**: Anthropic Claude, OpenAI GPT, Google Gemini, OpenRouter, Ollama, llama.cpp
- **Automatic Fallback**: Seamlessly switches between providers
- **Local Models**: Works offline with Ollama and llama.cpp

### 🔧 Self-Modifying Skills System
- **Built-in Skills**: File, shell, browser, scheduler operations
- **Custom Skills**: Create your own skills with Python
- **Self-Modification**: Skills can create and modify other skills
- **Permission System**: Fine-grained access control

### 🌐 Browser Automation
- **Playwright Integration**: Control browsers programmatically
- **Actions**: Navigate, click, type, screenshot, extract data
- **Headless Mode**: Run without GUI

### 💻 Computer Use & Vision
- **Screen Control**: Mouse and keyboard automation
- **Vision**: Screen understanding and analysis
- **Safety Guards**: Confirmation prompts for sensitive operations

### 🎨 Live Canvas UI
- **Real-time Updates**: WebSocket-based visual interface
- **Multiple Elements**: Text, markdown, code, images, charts
- **Multi-client Sync**: Share canvas across devices

### ⏰ Task Scheduler
- **Cron Support**: Standard cron expressions
- **Natural Language**: "@daily", "@hourly"
- **Async Execution**: Non-blocking task scheduling

### 💬 Telegram Bot
- **Full Integration**: Control ASTRO via Telegram
- **Authentication**: Access control for authorized users
- **Commands**: /skills, /canvas, /help

### 🔌 MCP Client
- **Model Context Protocol**: Connect to external tool servers
- **Auto-discovery**: MCP tools become ASTRO skills
- **Multiple Transports**: Stdio and SSE support

### 🤖 Sub-Agent Orchestration
- **Parallel Execution**: Run multiple agents simultaneously
- **Task Distribution**: Intelligent workload balancing
- **Result Aggregation**: Combine results from multiple agents

---

## 📥 Download & Install

### 🪟 Windows

**Option 1: Portable (Easiest)**
1. Download `ASTRO-AI-Assistant-Windows.zip` from [Releases](../../releases)
2. Extract to any folder
3. Double-click `ASTRO.bat` → Done! 🎉

**Option 2: System Install**
1. Download `ASTRO-AI-Assistant-Windows-Setup.zip`
2. Extract and run `Install-ASTRO.bat` as Administrator
3. Find ASTRO in your Start Menu

### 🐧 Linux (Ubuntu/Debian)

```bash
# Download the .deb package
wget https://github.com/Senpai-Sama7/Astro/releases/latest/download/astro-ai-assistant_1.0.0-alpha.0_all.deb

# Install
sudo dpkg -i astro-ai-assistant_*.deb
sudo apt-get install -f  # Fix any dependencies

# Launch
astro-desktop        # Web interface
astro-shell          # Local AI shell (no internet needed)
astro-vibe           # Advanced AI shell (requires API key)
```

### 🍎 macOS

```bash
# Clone and run
git clone https://github.com/Senpai-Sama7/Astro.git
cd Astro
npm install && npm run build
npm start
```

### 🐳 Docker (Any Platform)

```bash
# One-liner setup
git clone https://github.com/Senpai-Sama7/Astro.git && cd Astro
cp .env.example .env  # Edit with your settings
docker-compose up
```

---

## 🚀 Quick Start

### Step 1: Launch ASTRO
- **Web Interface**: Open http://localhost:5000 in your browser
- **Desktop App**: Double-click the ASTRO icon
- **Terminal**: Run `astro-shell` for command-line mode

### Step 2: Start Chatting!

Just type what you want in plain English:

**💼 For Work:**
- *"Schedule a meeting with the team for tomorrow at 2pm"*
- *"Find all invoices from last month"*
- *"Convert this PDF to text"*

**💻 For Coding:**
- *"Run my tests and show me what failed"*
- *"Check my code for security issues"*
- *"Generate a README for this project"*

**🏠 For Personal:**
- *"Organize my photos by date"*
- *"What's 25% off $129.99?"*
- *"Remind me to call mom every Sunday"*

**🔍 For Research:**
- *"Search for latest React tutorials"*
- *"Summarize this article"*
- *"Compare TypeScript vs JavaScript"*

---

## ✨ Features at a Glance

### 🗂️ File Management
```
You: "Show me all files over 50MB in my Downloads folder"
ASTRO: "I found 2 large files:
        • video.mp4 (1.2 GB) - 3 weeks old
        • backup.zip (340 MB) - 2 months old
        Would you like me to help you clean these up?"
```

### 🔍 Smart Search
```
You: "Find where I used the API key in my code"
ASTRO: "Found 'API_KEY' in 3 files:
        • src/config.js (line 12)
        • tests/auth.test.js (line 45)
        • .env.example (line 3) ← This one is safe"
```

### 🧮 Calculations & Conversions
```
You: "If I work 4 hours at $35/hour, how much do I make?"
You: "Convert 75°F to Celsius"
You: "What's the square root of 144 plus 20%?"
```

### 🧪 Code & Testing
```
You: "Run my project's tests"
You: "Check which dependencies need updating"
You: "Show me a summary of recent git changes"
```

---

## 🏗️ How ASTRO Works

ASTRO uses a **4-layer architecture** that keeps you safe while getting things done:

```
┌─────────────────────────────────────────────────────────────────────┐
│  👤 YOU                                                            │
│  "Run my tests and show me what failed"                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1️⃣ ARIA - The Translator 🗣️                                       │
│  Understands natural language • Maintains conversation context      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2️⃣ OTIS - The Guardian 🛡️                                         │
│  Checks permissions • Assesses risk • Logs for audit                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3️⃣ CORE - The Orchestrator ⚙️                                     │
│  Multi-provider LLM • Skills system • Sub-agent orchestration       │
│  Browser automation • Computer use • Task scheduling                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4️⃣ C0Di3 - The Watchdog 🐕                                        │
│  Monitors threats • Tracks vulnerabilities • Manages incidents      │
└─────────────────────────────────────────────────────────────────────┘
```

**Think of it like a smart office:**
- **ARIA** is your helpful receptionist who understands what you need
- **OTIS** is security, checking badges and logging who goes where
- **CORE** is the operations team with multi-provider AI, skills, and automation
- **C0Di3** is the security guard watching for threats

---

## 🛡️ Security First

We built ASTRO with security as the foundation, not an afterthought:

| Feature | What It Means For You |
|---------|----------------------|
| 🔒 **No Shell Injection** | ASTRO can't be tricked into running dangerous commands |
| 📁 **Sandboxed Files** | File access is restricted to your workspace only |
| 📝 **Audit Trails** | Every action is logged (tamper-evident) |
| 🔐 **RBAC** | Different users get different permissions |
| 🚫 **Command Blacklist** | Dangerous operations like `rm -rf /` are blocked |
| 🔍 **Input Validation** | All inputs checked before processing |
| 🔧 **Bandit Scanned** | Code scanned for security vulnerabilities |

**Your data stays yours.** ASTRO works locally by default. Cloud AI features are optional and require explicit API keys.

---

## 🖥️ Command Line Interfaces

For power users, ASTRO includes specialized shells:

### `astro_shell` - Local AI (No Internet Needed!)

```bash
$ astro_shell
🤖 ASTRO Shell (Local Mode)
Type 'help' for commands, 'exit' to quit.

> show me the README
📄 README.md (2.4 KB)
===================
ASTRO - Your AI Assistant...

> search for "TODO" in python files
🔍 Found 3 matches:
  • src/main.py:45: # TODO: Add error handling
  • src/utils.py:12: # TODO: Optimize this
```

**Perfect for:** Air-gapped environments, privacy-conscious users, offline work

### `astro_vibe` - Advanced AI (Cloud-Powered)

```bash
$ export ANTHROPIC_API_KEY=your_key_here
$ astro_vibe
🌟 ASTRO Vibe Shell (LLM Mode)

> analyze this codebase and suggest improvements
🤖 Analyzing...
📊 Code Quality Report:
   • Test coverage: 78% (recommend 85%+)
   • 2 unused dependencies found
   • 1 potential security issue in auth.js:23
```

**Perfect for:** Complex analysis, code reviews, research tasks

### `astro_core_cli` - Full Platform Access

```bash
$ python astro_core_cli.py

🚀 ASTRO Core Interactive Shell
Type 'help' for commands, 'exit' to quit.

astro> status
🟢 ASTRO Core Status:
  🤖 LLM: claude-3-sonnet-20240229
  🔧 Skills: 12 loaded
  📅 Scheduler: Running
  🎨 Canvas: ws://localhost:8765
```

**Perfect for:** Full platform access, skills management, automation

---

## 📊 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 / Ubuntu 20.04 / macOS 12 | Latest versions |
| **Node.js** | 18.x | 20.x LTS |
| **Python** | 3.11 | 3.12+ |
| **RAM** | 2 GB | 4 GB+ |
| **Disk** | 500 MB | 1 GB |

---

## 🧪 Testing & Quality

ASTRO is thoroughly tested with **248 automated tests**:

```bash
# Run all tests
npm test

# Python shell tests
python -m pytest tests/test_astro_shell.py tests/test_vibe_shell.py -v

# Code quality checks
ruff check src/
bandit -r src/ -x tests/ -ll -ii -s B101

# With coverage
npm run coverage
```

- ✅ 186 TypeScript tests (backend, API, agents)
- ✅ 52 Python tests (shell functionality, security)
- ✅ Security hardened with path traversal protection
- ✅ Dangerous command filtering
- ✅ Comprehensive audit logging
- ✅ Ruff code style compliance
- ✅ Bandit security scanning

---

## 🤔 Frequently Asked Questions

### General Questions

**Q: Do I need to know how to code to use ASTRO?**
> **A:** Not at all! ASTRO is designed for everyone. Just type what you want in plain English. For developers, there are advanced features available, but the basics work for anyone.

**Q: Is my data safe?**
> **A:** Yes. By default, everything stays on your computer. We don't send your files or conversations anywhere. Cloud AI features only activate if you explicitly add an API key.

**Q: Can ASTRO break my computer?**
> **A:** ASTRO has multiple safety layers. Dangerous commands like "delete everything" are blocked. File operations are sandboxed. And you can always see what ASTRO plans to do before it does it.

**Q: Does it work offline?**
> **A:** Yes! The `astro_shell` works completely offline using local AI. The `astro_vibe` shell requires internet for advanced features.

### Technical Questions

**Q: What LLMs does ASTRO support?**
> **A:** ASTRO Core supports 6 providers: Anthropic Claude, OpenAI GPT, Google Gemini, OpenRouter (100+ models), Ollama (local), and llama.cpp (custom models). Local mode uses rule-based AI (no LLM needed).

**Q: Can I add my own tools?**
> **A:** Yes! ASTRO has a powerful skills system. You can create custom skills in Python that can self-modify and create other skills. See `src/skills/builtin/skill_creator.py` for examples.

**Q: Is there an API?**
> **A:** Yes, a full REST API is available at `/api/v1/` with WebSocket support for real-time features. There's also a programmatic Python API via `AstroCore`.

**Q: How do I deploy to production?**
> **A:** Use Docker: `docker-compose up` or see our [Deployment Guide](./docs/deployment.md).

**Q: What is MCP?**
> **A:** MCP (Model Context Protocol) allows ASTRO to connect to external tool servers. MCP tools are automatically discovered and become available as ASTRO skills.

---

## 🗺️ Roadmap

| Version | Features | Status |
|---------|----------|--------|
| **1.0.0-alpha** | Core platform, basic agents, CLI shells | ✅ Current |
| **1.0.0-beta** | ASTRO Core: Multi-provider LLM, skills system, browser automation | ✅ Completed |
| **1.0.0** | Stable release, full documentation | 🚧 In Progress |
| **1.1.0** | Voice commands, mobile app, WhatsApp integration | 📅 Planned |
| **1.2.0** | Team collaboration features, advanced analytics | 📅 Planned |

---

## 🤝 Contributing

We welcome contributions! Whether you're a developer, designer, writer, or tester, there's a place for you.

### For Developers
```bash
# 1. Fork and clone
git clone https://github.com/YOUR-USERNAME/Astro.git

# 2. Install dependencies
npm install
python -m pip install -r requirements.txt

# 3. Create a branch
git checkout -b feature/amazing-feature

# 4. Make changes and test
npm test
python -m pytest tests/
ruff check src/
bandit -r src/ -x tests/ -ll -ii -s B101

# 5. Submit a PR
```

### For Non-Developers
- 📖 **Documentation** — Help improve guides and tutorials
- 🎨 **Design** — UI/UX improvements, icons, graphics
- 🐛 **Testing** — Try ASTRO and report bugs
- 🌍 **Translation** — Help translate to other languages
- 💡 **Ideas** — Suggest features and improvements

See [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

---

## 📞 Support & Community

| Channel | Link |
|---------|------|
| 💬 **Discord** | [Join our community](https://discord.gg/astro-ai) |
| 🐛 **Bug Reports** | [GitHub Issues](../../issues) |
| 📧 **Email** | support@astro-ai.dev |
| 📚 **Documentation** | [docs.astro-ai.dev](https://docs.astro-ai.dev) |

---

## 📜 License

MIT License — See [LICENSE](./LICENSE) for details.

**Commercial Use:** ASTRO is free for personal and commercial use. Attribution appreciated but not required.

---

## 🙏 Acknowledgments

ASTRO builds on amazing open-source projects:

- **Node.js & Express** — Web foundation
- **Socket.IO** — Real-time communication
- **Python & asyncio** — Shell architecture
- **Anthropic, OpenAI, Google** — LLM providers
- **Playwright** — Browser automation
- **And 100+ more** — See [package.json](./package.json)

---

<div align="center">

## ⭐ Star Us on GitHub!

If ASTRO helps you, please give us a star! It helps others find the project.

[![Star History Chart](https://api.star-history.com/svg?repos=Senpai-Sama7/Astro&type=Date)](https://star-history.com/#Senpai-Sama7/Astro&Date)

**Made with ❤️ by [Douglas Mitchell](https://github.com/Senpai-Sama7)**

[🔝 Back to Top](#-astro)

</div>
