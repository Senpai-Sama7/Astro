<div align="center">

# 🌟 ASTRO - Autonomous Agent Ecosystem

### *Your Personal AI Team That Actually Gets Things Done*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Senpai-Sama7/autonomous-agent-ecosystem/pulls)

<img src="https://img.shields.io/badge/AI%20Powered-OpenAI%20|%20Ollama%20|%20OpenRouter-purple" alt="AI Powered">

---

**Imagine having a team of AI assistants that can research the internet, write code, and manage your files — all from a single command in plain English.**

[Get Started](#-quick-start-5-minutes) • [Watch Demo](#-see-it-in-action) • [User Guide](#-complete-user-guide) • [FAQ](#-frequently-asked-questions)

</div>

---

## 🎬 See It In Action

```
You: "Research the latest trends in AI and create a summary report"

🔍 Research Agent: Searching the web...
📝 Research Agent: Found 6 relevant sources
💾 FileSystem Agent: Created reports/ai_trends_2025.md
✅ Done! Your report is ready.
```

**That's it.** No complex commands. No programming required. Just tell it what you want.

---

## ✨ What Can ASTRO Do For You?

<table>
<tr>
<td width="33%" align="center">

### 🔬 Research Agent
**Your Personal Researcher**

- Searches the entire internet
- Reads and summarizes articles
- Finds the information you need

*"Find me the best pizza recipe"*

</td>
<td width="33%" align="center">

### 💻 Code Agent
**Your AI Programmer**

- Writes Python code for you
- Runs and tests the code
- Fixes bugs automatically

*"Create a script to organize my photos"*

</td>
<td width="33%" align="center">

### 📁 File Agent
**Your Digital Secretary**

- Creates and edits files
- Organizes your documents
- Saves reports and summaries

*"Save this summary to my reports folder"*

</td>
</tr>
</table>

---

## 🚀 Quick Start (5 Minutes)

### What You'll Need

- ✅ A computer (Windows, Mac, or Linux)
- ✅ Python installed ([Download here](https://python.org/downloads) if you don't have it)
- ✅ An API key (free options available!)

### Step 1: Download ASTRO

**Option A: Download ZIP** (Easiest)
1. Click the green "Code" button above
2. Click "Download ZIP"
3. Extract the folder to your Desktop

**Option B: Use Git** (For developers)
```bash
git clone https://github.com/Senpai-Sama7/autonomous-agent-ecosystem.git
cd autonomous-agent-ecosystem
```

### Step 2: Install Requirements

Open your terminal (Command Prompt on Windows, Terminal on Mac) and run:

```bash
pip install -r requirements.txt
```

> 💡 **Tip**: If you see an error, try `pip3` instead of `pip`

### Step 3: Set Up Your AI Provider

Choose ONE of these options:

<details>
<summary><b>🆓 Option A: Use Ollama (FREE - Runs on Your Computer)</b></summary>

1. Download Ollama from [ollama.ai](https://ollama.ai)
2. Install it (just double-click the installer)
3. Open terminal and run: `ollama pull llama3`
4. That's it! No API key needed.

</details>

<details>
<summary><b>💳 Option B: Use OpenAI (Best Quality)</b></summary>

1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an account and add billing
3. Go to API Keys and create a new key
4. Create a file named `.env` in the ASTRO folder with:
```
OPENAI_API_KEY=sk-your-key-here
```

</details>

<details>
<summary><b>🔄 Option C: Use OpenRouter (Many Models)</b></summary>

1. Go to [openrouter.ai](https://openrouter.ai)
2. Create an account
3. Get your API key
4. Create a file named `.env` in the ASTRO folder with:
```
OPENROUTER_API_KEY=your-key-here
```

</details>

### Step 4: Launch ASTRO!

**For the Beautiful GUI (Recommended):**
```bash
python src/gui_app.py
```

**For Command Line:**
```bash
python src/main.py --interactive
```

🎉 **Congratulations!** You're ready to use your personal AI team!

---

## 📖 Complete User Guide

### Using the Desktop App (GUI)

When you launch `gui_app.py`, you'll see a beautiful dark-themed interface:

```
┌─────────────────────────────────────────────────────────────┐
│  AGENT ECO                              [System Online 🟢]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  💬 Ask Your Agents                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Type your command here...                       [▶] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📡 System Activity          │  📜 Workflow History        │
│  ─────────────────────────── │  ────────────────────────   │
│  10:30 - Research started... │  🟡 Research AI trends      │
│  10:31 - Found 5 sources...  │  ✅ Generate report         │
│  10:32 - Task completed ✅   │  ⏳ File organization       │
│                              │                             │
└─────────────────────────────────────────────────────────────┘
```

**How to Use:**

1. **Click "🚀 Start System"** - Wait for "System Online" to appear
2. **Type your request** - Use plain English, like talking to a person
3. **Press Enter or click "Execute ▶"** - Watch the magic happen
4. **See results** - Check the Activity log and your files

### Example Commands You Can Try

| What You Want | What to Type |
|---------------|--------------|
| Search the web | *"Search for the best laptop under $1000"* |
| Create a file | *"Create a file called notes.txt with my meeting notes"* |
| Write code | *"Write a Python script that calculates my monthly budget"* |
| Research + Save | *"Research climate change and save a summary to climate_report.md"* |
| Complex tasks | *"Find Python tutorials, summarize the best ones, and save to learning_path.md"* |

### Understanding the Interface

| Section | What It Shows |
|---------|---------------|
| **System Status** (top-left) | 🟢 Green = Running, ⚫ Gray = Offline |
| **Agent Cards** (left sidebar) | Shows each AI agent and what it's doing |
| **Command Input** (top) | Where you type your requests |
| **System Activity** (bottom-left) | Live log of what's happening |
| **Workflow History** (bottom-right) | List of your past commands |

### Settings & Configuration

Click **"⚙️ Settings"** to configure:

- **Provider**: Choose your AI (OpenAI, Ollama, or OpenRouter)
- **Model**: Select which AI model to use
- **API Key**: Enter your API key (hidden for security)

---

## 🎯 Tips for Best Results

### ✅ DO: Be Specific
```
Good: "Search for Python tutorials for beginners and save the top 5 to tutorials.md"
Bad:  "Find stuff"
```

### ✅ DO: Use Natural Language
```
Good: "Create a summary of today's tech news"
Good: "Help me write code to sort a list of names"
Bad:  "RUN_SEARCH --query='tech' --output=summary"
```

### ✅ DO: Chain Tasks Together
```
"Research machine learning, then create a Python example, and save everything to ml_notes.md"
```

### ❌ DON'T: Ask for Harmful Content
The system has built-in safety measures and won't:
- Access files outside the workspace folder
- Run dangerous code
- Perform harmful searches

---

## ❓ Frequently Asked Questions

<details>
<summary><b>Is my data safe?</b></summary>

Yes! ASTRO:
- Only accesses files in the `workspace` folder
- Never sends your files to the internet
- Keeps API keys encrypted locally
- Runs code in a secure sandbox

</details>

<details>
<summary><b>Do I need to pay?</b></summary>

Not necessarily! You have free options:
- **Ollama**: Completely free, runs on your computer
- **OpenAI**: Pay-per-use, usually pennies per request
- **OpenRouter**: Some free models available

</details>

<details>
<summary><b>Why isn't it working?</b></summary>

Try these fixes:

1. **"Module not found" error**: Run `pip install -r requirements.txt` again
2. **"API key invalid" error**: Check your `.env` file has the correct key
3. **"System Offline"**: Click "🚀 Start System" first
4. **Slow responses**: Ollama is slower than cloud APIs - this is normal

</details>

<details>
<summary><b>Can I use this for my business?</b></summary>

Yes! ASTRO is MIT licensed, meaning you can:
- ✅ Use it commercially
- ✅ Modify it for your needs
- ✅ Distribute it
- Just keep the license notice

</details>

<details>
<summary><b>How do I update ASTRO?</b></summary>

```bash
git pull origin main
pip install -r requirements.txt
```

Or download the latest ZIP from GitHub.

</details>

---

## 🏗️ How It Works (For the Curious)

```
                    ┌─────────────────────┐
                    │    Your Command     │
                    │  "Research AI..."   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Natural Language  │
                    │     Interpreter     │
                    │  (Understands you)  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Agent Engine     │
                    │ (The Brain/Manager) │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
   ┌──────▼──────┐     ┌───────▼──────┐    ┌───────▼──────┐
   │  Research   │     │     Code     │    │  FileSystem  │
   │   Agent     │     │    Agent     │    │    Agent     │
   │ 🔍 Search   │     │ 💻 Program   │    │ 📁 Files     │
   └─────────────┘     └──────────────┘    └──────────────┘
```

**The magic happens in 4 steps:**

1. **You speak naturally** → "Find me information about..."
2. **AI understands** → Converts your words into tasks
3. **Agents work together** → Each specialist does their part
4. **Results delivered** → Files created, code run, answers found

---

## 🛠️ Advanced Configuration

### For Power Users

Edit `config/system_config.yaml`:

```yaml
system:
  environment: "production"    # or "development" for more logs
  log_level: "INFO"           # DEBUG, INFO, WARNING, ERROR
  max_concurrent_workflows: 10 # How many tasks at once

llm:
  provider: "openai"          # openai, ollama, openrouter
  model_name: "gpt-4"         # Your preferred model
  timeout: 60                 # Seconds to wait for response
```

### Agent-Specific Settings

Edit `config/agents.yaml`:

```yaml
research_agent_001:
  max_search_results: 10      # More results = more thorough
  max_pages_to_scrape: 5      # Pages to read in full

code_agent_001:
  safe_mode: true             # Keep this ON for security
  max_code_length: 10000      # Maximum code size

filesystem_agent_001:
  root_dir: "./workspace"     # Where files are saved
  allowed_extensions:         # What files can be created
    - .txt
    - .py
    - .md
    - .json
```

---

## 📁 Project Structure

```
astro/
├── 📁 config/                 # Settings files
│   ├── system_config.yaml    # Main configuration
│   └── agents.yaml           # Agent-specific settings
│
├── 📁 src/                    # Source code
│   ├── 📁 agents/            # The AI workers
│   │   ├── research_agent.py # Searches the web
│   │   ├── code_agent.py     # Writes code
│   │   └── filesystem_agent.py # Manages files
│   │
│   ├── 📁 core/              # The brain
│   │   ├── engine.py         # Task manager
│   │   └── nl_interface.py   # Understands you
│   │
│   ├── main.py               # Command-line version
│   └── gui_app.py            # Desktop app
│
├── 📁 workspace/              # Your files go here
├── 📁 tests/                  # Quality checks
├── requirements.txt          # Dependencies
└── README.md                 # You are here!
```

---

## 🆘 Getting Help

**Something not working?** Here's how to get help:

1. 📖 Check the [FAQ](#-frequently-asked-questions) above
2. 🔍 Search [existing issues](https://github.com/Senpai-Sama7/autonomous-agent-ecosystem/issues)
3. 🐛 [Report a bug](https://github.com/Senpai-Sama7/autonomous-agent-ecosystem/issues/new)
4. 💬 [Start a discussion](https://github.com/Senpai-Sama7/autonomous-agent-ecosystem/discussions)

---

## 🤝 Contributing

We love contributions! Whether it's:

- 🐛 Bug fixes
- ✨ New features
- 📖 Documentation improvements
- 🎨 UI enhancements

See our [Contributing Guide](CONTRIBUTING.md) to get started.

---

## 📄 License

MIT License - Use it freely, modify it, share it!

---

<div align="center">

### Made with ❤️ by the ASTRO Team

**[⬆ Back to Top](#-astro---autonomous-agent-ecosystem)**

</div>
