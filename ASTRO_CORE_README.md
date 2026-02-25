# 🤖 ASTRO Core - Enhanced AI Platform

ASTRO Core is a comprehensive AI assistant platform with advanced capabilities for automation, code generation, and multi-modal interaction.

## ✨ New Features

### 1. 🧠 Universal LLM Support
Connect to any LLM provider with automatic fallback:

| Provider | Setup | Best For |
|----------|-------|----------|
| **OpenAI** | `OPENAI_API_KEY` | General purpose |
| **Anthropic** | `ANTHROPIC_API_KEY` | Complex reasoning |
| **Google Gemini** | `GOOGLE_API_KEY` | Multimodal tasks |
| **OpenRouter** | `OPENROUTER_API_KEY` | Access 100+ models |
| **Ollama** | Local install | Privacy, offline |
| **llama.cpp** | Local server | Custom models |

```python
# Auto-detects available providers with fallback
astro = AstroCore()
await astro.initialize()

# Or specify priority
config = {"llm_priority": ["anthropic", "openai", "ollama"]}
astro = AstroCore(config)
```

### 2. 🔧 Skills System with Self-Modification
Create, modify, and manage skills dynamically:

```python
# Create skill from description
result = await astro.skills.create_skill_from_description(
    "Fetch weather data for a city",
    "weather_fetcher",
    context
)

# Execute skills
result = await astro.skills.execute_skill(
    "file",
    {"action": "list", "path": "."},
    context
)

# Built-in skills:
# - file: Read/write/list files
# - shell: Execute shell commands (safe)
# - browser: Web automation
# - scheduler: Cron jobs
# - skill_creator: Create new skills
```

### 3. 🌐 Browser Automation
Control a browser programmatically:

```python
# Navigate
await astro.browser_goto("https://example.com")

# Or via skill
result = await astro.skills.execute_skill("browser", {
    "action": "goto",
    "url": "https://example.com"
})

# Screenshot
await astro.skills.execute_skill("browser", {
    "action": "screenshot",
    "output_path": "screenshot.png"
})

# Extract data
result = await astro.skills.execute_skill("browser", {
    "action": "extract",
    "selector": "h1"
})
```

### 4. 💻 Computer Use (Mouse/Keyboard)
Control your computer:

```python
# Requires: pip install pyautogui

from src.computer import ComputerController

controller = ComputerController()

# Click at position
await controller.execute("click", x=100, y=200)

# Type text
await controller.execute("type", text="Hello, World!")

# Take screenshot
result = await controller.execute("screenshot", path="screen.png")

# Press hotkey
await controller.execute("hotkey", keys=["ctrl", "s"])
```

### 5. 🎨 Live Canvas/UI
Real-time visual workspace:

```python
# Create canvas
canvas = astro.create_canvas("My Project")

# Add elements
from src.canvas import CanvasElement, ElementType

element = CanvasElement.create(
    type=ElementType.MARKDOWN,
    content="# Project Status\n\nEverything is on track!",
    x=50, y=50
)
canvas.add_element(element)

# WebSocket server auto-starts
# Open: ws://localhost:8765/{canvas_id}
```

### 6. ⏰ Task Scheduler
Cron-like scheduling:

```python
# Schedule skill execution
result = await astro.schedule_task(
    name="Daily Backup",
    schedule="@daily",  # or "0 9 * * *" for 9am
    skill_name="file",
    skill_params={"action": "list", "path": "/backup"}
)

# Via chat
await astro.chat("/schedule add 'Hourly Check' @hourly shell 'df -h'")
```

### 7. 💬 Telegram Bot
Control ASTRO via Telegram:

```bash
# Set environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_ALLOWED_USERS="user_id1,user_id2"  # Optional

# Auto-starts with ASTRO Core
```

**Bot Commands:**
- `/start` - Welcome message
- `/skills` - List available skills
- `/canvas` - Create live canvas
- `/help` - Show help

### 8. 🔌 MCP (Model Context Protocol)
Connect to MCP servers:

```python
# Connect to MCP server
await astro.mcp.connect_stdio(
    server_id="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path"]
)

# MCP tools auto-register as skills
result = await astro.skills.execute_skill(
    "mcp_read_file",
    {"path": "/some/file.txt"}
)
```

### 9. 🤖 Sub-Agent Orchestration
Spawn specialized agents for parallel tasks:

```python
# Create specialized agents
code_agent = astro.agents.create_agent(
    name="Code Reviewer",
    agent_type="code",
    system_prompt="You are an expert code reviewer..."
)

# Submit tasks
await astro.agents.submit_task(
    description="Review src/main.py for security issues",
    agent_type="code"
)

# Parallel execution
tasks = [
    "Analyze code",
    "Write tests",
    "Update docs"
]
results = await astro.agents.execute_parallel(tasks)
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Senpai-Sama7/Astro.git
cd Astro

# Install dependencies
pip install -r requirements.txt

# Optional: Install specific features
pip install playwright pyautogui python-telegram-bot websockets croniter mcp
playwright install
```

### Environment Setup

```bash
# Create .env file
cat > .env << EOF
# LLM Providers (at least one)
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key

# Optional
TELEGRAM_BOT_TOKEN=your_bot_token
OLLAMA_HOST=http://localhost:11434

# ASTRO Config
ASTRO_LLM_PRIORITY=anthropic,openai,ollama
EOF
```

### Usage

```python
import asyncio
from src.astro_core import AstroCore

async def main():
    # Initialize
    astro = AstroCore()
    await astro.initialize()
    
    # Chat
    response = await astro.chat("What can you do?")
    print(response)
    
    # Create skill
    result = await astro.skills.create_skill_from_description(
        "Calculate fibonacci numbers",
        "fibonacci",
        context
    )
    
    # Use sub-agent
    result = await astro.execute_task(
        "Analyze the codebase",
        agent_type="code",
        use_sub_agent=True
    )
    
    # Cleanup
    await astro.shutdown()

asyncio.run(main())
```

### CLI Usage

```bash
# Interactive mode
python astro_core_cli.py

# Single command
python astro_core_cli.py "list files in current directory"

# Use skills
python astro_core_cli.py "/file list ."
python astro_core_cli.py "/browser goto https://example.com"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     ASTRO Core                          │
├─────────────────────────────────────────────────────────┤
│  🧠 LLM          │ Universal provider interface         │
│  🔧 Skills       │ Self-modifying plugin system         │
│  🌐 Browser      │ Playwright automation                │
│  💻 Computer     │ Mouse/keyboard control               │
│  🎨 Canvas       │ Live WebSocket UI                    │
│  ⏰ Scheduler    │ Cron-like task scheduling            │
│  💬 Telegram     │ Bot integration                      │
│  🔌 MCP          │ Model Context Protocol               │
│  🤖 Agents       │ Sub-agent orchestration              │
└─────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
src/
├── llm/              # Universal LLM providers
│   ├── provider.py
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── google_provider.py
│   ├── openrouter_provider.py
│   ├── ollama_provider.py
│   ├── llamacpp_provider.py
│   └── factory.py
├── skills/           # Plugin system
│   ├── skill.py
│   ├── registry.py
│   ├── manager.py
│   └── builtin/      # Built-in skills
├── browser/          # Browser automation
├── computer/         # Computer control
├── canvas/           # Live UI
├── scheduler/        # Task scheduling
├── channels/         # Telegram/ messaging
├── mcp/              # MCP client
├── agents/           # Sub-agent orchestration
└── astro_core.py     # Main integration
```

## 🔒 Security

- Path traversal protection
- Dangerous command filtering
- Permission-based skill execution
- Sandboxed file operations
- Audit logging

## 🧪 Testing

```bash
# Run tests
pytest tests/test_llm/ -v
pytest tests/test_skills/ -v

# With coverage
pytest --cov=src tests/
```

## 📝 License

MIT License - See LICENSE file
