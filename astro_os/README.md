# Astro-OS: Autonomous TUI Agent for Linux

A production-grade, autonomous terminal agent with a 3-panel TUI dashboard, designed for Lubuntu and Kali Linux.

## Features

### 🖥️ TUI Dashboard (Textual)
- **Left Panel**: Streaming markdown chat with syntax highlighting
- **Right Panel**: Live execution logs (shell & browser activity)
- **Footer**: Status bar with Mode, Session ID, and CWD

### 🔧 Shell Tool (Self-Healing)
- Automatic permission detection (sudo escalation suggestions)
- Kali Linux security tools support (nmap, aircrack, etc.)
- Command history and result injection
- Ghost commands: agent suggests, you confirm with Enter

### 🌐 Browser Tool (Vision-Guided)
- Playwright with stealth mode
- Multimodal vision for obfuscated UIs
- Screenshot analysis for element location
- Automatic fallback from CSS selectors to vision

### 🧠 Memory (Claude Code Brain)
- Recursive project indexer (README, package.json, structure)
- Persistent state.json across restarts
- Conversation context management
- Project-aware responses

## Installation

```bash
cd astro_os
pip install -r requirements.txt

# For browser automation
playwright install chromium
```

## Usage

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."
# Or for Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: specify model
export ASTRO_MODEL="gpt-4o"

# Run
python main.py
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Submit input / Confirm ghost command |
| `Escape` | Cancel ghost command |
| `Ctrl+C` | Interrupt running task |
| `Ctrl+Q` | Quit application |
| `Ctrl+L` | Clear execution logs |
| `Ctrl+M` | Toggle Shell/Web mode |
| `Ctrl+P` | Index current project |

## Ghost Commands

When Astro suggests a command, it appears in your input field as a "ghost command":
1. Press `Enter` to execute as-is
2. Edit the command and press `Enter`
3. Press `Escape` to cancel

## Direct Commands

Prefix with `!` to execute shell commands directly:
```
!ls -la
!nmap -sV localhost
```

## Kali Linux Compatibility

Astro-OS recognizes common security tools and will:
- Suggest sudo when needed (nmap, tcpdump, aircrack-ng, etc.)
- Mark dangerous operations for confirmation
- Provide self-healing suggestions for permission errors

## Project Structure

```
astro_os/
├── main.py           # TUI application (Textual)
├── requirements.txt  # Dependencies
├── tools/
│   ├── shell.py      # Self-healing shell executor
│   └── browser.py    # Vision-guided browser automation
└── memory/
    └── context.py    # Recursive context loader & state
```

## State Persistence

Session state is saved to `~/.astro_os_state.json`:
- Conversation history
- Command history
- Indexed project contexts
- Current working directory
- Mode (shell/web)
