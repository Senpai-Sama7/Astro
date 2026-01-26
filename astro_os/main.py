#!/usr/bin/env python3
"""
Astro-OS: Production-grade Autonomous TUI Agent.

Enhanced 3-panel dashboard with streaming chat, live execution logs, and ghost commands.
"""

import os
import sys
import json
import asyncio
import platform
from datetime import datetime
from typing import Optional, List, Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, RichLog, Markdown, Button, Label, ProgressBar
from textual.binding import Binding
from textual.message import Message
from textual import work
from textual.reactive import reactive
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from astro_os.tools import ShellTool, BrowserTool
    from astro_os.memory import Memory
except ImportError:
    ShellTool = None
    BrowserTool = None
    Memory = None

# LLM Client
try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


SYSTEM_PROMPT = """You are Astro-OS, an autonomous Linux terminal agent running on {os_info}.
You have two modes: Shell (execute commands) and Web (browser automation).

## Current Context
{context}

## Response Format
ALWAYS respond with valid JSON:

### For shell commands:
{{"mode": "shell", "thought": "reasoning", "command": "bash command", "dangerous": false}}

### For web actions:
{{"mode": "web", "thought": "reasoning", "action": "navigate|click|type", "target": "url or selector", "value": "optional text"}}

### For information/conversation:
{{"mode": "chat", "thought": "your response", "command": null}}

### For multi-step plans:
{{"mode": "plan", "thought": "overview", "steps": [{{"action": "shell|web", "command": "...", "description": "..."}}]}}

## Rules
1. Output ONLY valid JSON
2. Set dangerous=true for: rm -rf, sudo, system changes, security tools
3. For Kali tools (nmap, aircrack, etc), always note they may need sudo
4. Analyze command output and continue reasoning
5. Use web mode for browsing, shell mode for local operations"""


class StatusBar(Static):
    """Status bar showing system info."""
    
    mode = reactive("shell")
    status = reactive("ready")
    
    def render(self) -> Text:
        mode_color = "green" if self.mode == "shell" else "blue"
        status_color = "green" if self.status == "ready" else "yellow"
        
        text = Text()
        text.append("⚡ ", style="bold yellow")
        text.append("ASTRO-OS", style="bold cyan")
        text.append(" │ ", style="dim")
        text.append(f"Mode: ", style="dim")
        text.append(f"{self.mode.upper()}", style=f"bold {mode_color}")
        text.append(" │ ", style="dim")
        text.append(f"Status: ", style="dim")
        text.append(f"{self.status}", style=f"bold {status_color}")
        text.append(" │ ", style="dim")
        text.append(f"{platform.system()} {platform.release()}", style="dim")
        return text


class AgentCard(Static):
    """Card showing agent info."""
    
    def __init__(self, name: str, tools: List[str], status: str = "online", **kwargs):
        super().__init__(**kwargs)
        self.agent_name = name
        self.tools = tools
        self.agent_status = status
    
    def render(self) -> Panel:
        status_icon = "🟢" if self.agent_status == "online" else "🔴"
        content = f"{status_icon} {self.agent_name}\n"
        content += f"[dim]Tools: {', '.join(self.tools[:3])}{'...' if len(self.tools) > 3 else ''}[/dim]"
        return Panel(content, border_style="cyan", padding=(0, 1))


class GhostCommandWidget(Static):
    """Widget showing suggested command."""
    
    command = reactive("")
    
    def render(self) -> Panel:
        if not self.command:
            return Panel("[dim]No suggestion[/dim]", title="💡 Ghost Command", border_style="dim")
        return Panel(
            f"[bold yellow]{self.command}[/bold yellow]\n[dim]Press Enter to execute, Esc to cancel[/dim]",
            title="💡 Ghost Command",
            border_style="yellow"
        )


class AstroOS(App):
    """Astro-OS TUI Application - Enhanced UI/UX."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    #left-panel {
        width: 70%;
        height: 100%;
        border: solid $primary;
        padding: 0 1;
    }
    
    #right-panel {
        width: 30%;
        height: 100%;
        border: solid $secondary;
        padding: 0 1;
    }
    
    #status-bar {
        height: 1;
        background: $primary-darken-2;
        padding: 0 1;
    }
    
    #chat-container {
        height: 1fr;
    }
    
    #chat-log {
        height: 1fr;
        scrollbar-gutter: stable;
        border: round $primary-lighten-1;
        padding: 1;
    }
    
    #ghost-command {
        height: auto;
        margin: 1 0;
    }
    
    #input-container {
        height: auto;
        padding: 1 0;
    }
    
    #user-input {
        width: 100%;
        border: tall $accent;
    }
    
    #user-input:focus {
        border: tall $success;
    }
    
    #exec-log {
        height: 2fr;
        scrollbar-gutter: stable;
        border: round $secondary-lighten-1;
        padding: 1;
    }
    
    #agents-container {
        height: 1fr;
        padding: 1 0;
    }
    
    .agent-card {
        margin: 0 0 1 0;
    }
    
    .message {
        margin: 1 0;
        padding: 1;
    }
    
    .user-message {
        background: $success-darken-3;
        border-left: thick $success;
    }
    
    .assistant-message {
        background: $primary-darken-3;
        border-left: thick $primary;
    }
    
    .error-message {
        background: $error-darken-3;
        border-left: thick $error;
    }
    
    Header {
        background: $primary;
    }
    
    Footer {
        background: $primary-darken-2;
    }
    
    #title-bar {
        text-align: center;
        text-style: bold;
        color: $text;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "interrupt", "Interrupt", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_logs", "Clear", show=True),
        Binding("ctrl+m", "toggle_mode", "Mode", show=True),
        Binding("ctrl+p", "index_project", "Index", show=True),
        Binding("ctrl+r", "refresh", "Refresh", show=True),
        Binding("escape", "cancel_ghost", "Cancel", show=False),
        Binding("enter", "submit", "Submit", show=False),
        Binding("tab", "accept_ghost", "Accept Ghost", show=False),
    ]
    
    TITLE = "⚡ ASTRO-OS"
    SUB_TITLE = "Autonomous Terminal Agent"
    
    mode = reactive("shell")
    ghost_command = reactive("")
    is_processing = reactive(False)
    
    def __init__(self):
        super().__init__()
        self.conversation: List[Dict[str, str]] = []
        self.shell = ShellTool() if ShellTool else None
        self.browser = BrowserTool() if BrowserTool else None
        self.memory = Memory() if Memory else None
        self.llm_client = None
        self._setup_llm()
    
    def _setup_llm(self):
        """Setup LLM client."""
        if HAS_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY"):
            self.llm_client = anthropic.AsyncAnthropic()
            self.llm_provider = "anthropic"
        elif HAS_OPENAI:
            base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
            self.llm_client = AsyncOpenAI(base_url=base_url, api_key="ollama")
            self.llm_provider = "openai"
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="main-container"):
            # Left panel - Chat
            with Vertical(id="left-panel"):
                yield StatusBar(id="status-bar")
                yield Static("[bold cyan]💬 Chat[/bold cyan]", id="title-bar")
                
                with ScrollableContainer(id="chat-container"):
                    yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
                
                yield GhostCommandWidget(id="ghost-command")
                
                with Container(id="input-container"):
                    yield Input(placeholder="Ask Astro anything... (Ctrl+M to toggle mode)", id="user-input")
            
            # Right panel - Execution & Agents
            with Vertical(id="right-panel"):
                yield Static("[bold green]📟 Execution Log[/bold green]")
                yield RichLog(id="exec-log", highlight=True, markup=True, wrap=True)
                
                yield Static("[bold magenta]🤖 Agents[/bold magenta]")
                with ScrollableContainer(id="agents-container"):
                    yield AgentCard("Research Agent", ["web_search", "content_extract"], classes="agent-card")
                    yield AgentCard("Code Agent", ["echo", "math_eval"], classes="agent-card")
                    yield AgentCard("FileSystem Agent", ["read_file", "write_file"], classes="agent-card")
                    yield AgentCard("Git Agent", ["git_status", "git_diff"], classes="agent-card")
                    yield AgentCard("Shell Agent", ["execute", "sudo"], classes="agent-card")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.log_chat("system", "🚀 Welcome to Astro-OS!")
        self.log_chat("system", f"Mode: [bold]{self.mode.upper()}[/bold] | LLM: {getattr(self, 'llm_provider', 'none')}")
        self.log_chat("system", "Type your request or use Ctrl+M to toggle mode.")
        self.log_exec("[dim]Execution log ready...[/dim]")
        
        # Focus input
        self.query_one("#user-input", Input).focus()
    
    def log_chat(self, role: str, content: str) -> None:
        """Log a message to chat."""
        chat_log = self.query_one("#chat-log", RichLog)
        
        if role == "user":
            chat_log.write(Panel(content, title="🧑 You", border_style="green", padding=(0, 1)))
        elif role == "assistant":
            chat_log.write(Panel(content, title="🤖 Astro", border_style="cyan", padding=(0, 1)))
        elif role == "system":
            chat_log.write(f"[dim]{content}[/dim]")
        elif role == "error":
            chat_log.write(Panel(content, title="❌ Error", border_style="red", padding=(0, 1)))
    
    def log_exec(self, content: str) -> None:
        """Log to execution panel."""
        exec_log = self.query_one("#exec-log", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        exec_log.write(f"[dim]{timestamp}[/dim] {content}")
    
    def action_toggle_mode(self) -> None:
        """Toggle between shell and web mode."""
        self.mode = "web" if self.mode == "shell" else "shell"
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.mode = self.mode
        self.log_exec(f"Mode switched to [bold]{self.mode.upper()}[/bold]")
    
    def action_clear_logs(self) -> None:
        """Clear all logs."""
        self.query_one("#chat-log", RichLog).clear()
        self.query_one("#exec-log", RichLog).clear()
        self.log_chat("system", "Logs cleared.")
    
    def action_interrupt(self) -> None:
        """Interrupt current operation."""
        self.is_processing = False
        self.log_exec("[yellow]Operation interrupted[/yellow]")
    
    def action_cancel_ghost(self) -> None:
        """Cancel ghost command."""
        self.ghost_command = ""
        ghost_widget = self.query_one("#ghost-command", GhostCommandWidget)
        ghost_widget.command = ""
    
    def action_accept_ghost(self) -> None:
        """Accept and execute ghost command."""
        if self.ghost_command:
            self._execute_command(self.ghost_command)
            self.ghost_command = ""
            ghost_widget = self.query_one("#ghost-command", GhostCommandWidget)
            ghost_widget.command = ""
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        user_input = event.value.strip()
        if not user_input:
            return
        
        # Clear input
        event.input.value = ""
        
        # If ghost command is active, execute it
        if self.ghost_command:
            self._execute_command(self.ghost_command)
            self.ghost_command = ""
            self.query_one("#ghost-command", GhostCommandWidget).command = ""
            return
        
        # Process user input
        self.log_chat("user", user_input)
        self.conversation.append({"role": "user", "content": user_input})
        
        # Update status
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.status = "thinking..."
        self.is_processing = True
        
        # Process with LLM
        self._process_input(user_input)
    
    @work(exclusive=True)
    async def _process_input(self, user_input: str) -> None:
        """Process user input with LLM."""
        try:
            if not self.llm_client:
                self.log_chat("assistant", "No LLM configured. Set ANTHROPIC_API_KEY or use local Ollama.")
                return
            
            # Build context
            context = f"Mode: {self.mode}\nCWD: {os.getcwd()}"
            if self.memory:
                context += f"\nMemory: {self.memory.get_summary()}"
            
            system = SYSTEM_PROMPT.format(
                os_info=f"{platform.system()} {platform.release()}",
                context=context
            )
            
            # Call LLM
            self.log_exec("Calling LLM...")
            
            if self.llm_provider == "anthropic":
                response = await self.llm_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2048,
                    system=system,
                    messages=self.conversation[-10:]  # Last 10 messages
                )
                content = response.content[0].text
            else:
                response = await self.llm_client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "llama3.2"),
                    messages=[{"role": "system", "content": system}] + self.conversation[-10:],
                    max_tokens=2048
                )
                content = response.choices[0].message.content
            
            # Parse response
            await self._handle_response(content)
            
        except Exception as e:
            self.log_chat("error", f"Error: {str(e)}")
            self.log_exec(f"[red]Error: {str(e)}[/red]")
        finally:
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.status = "ready"
            self.is_processing = False
    
    async def _handle_response(self, content: str) -> None:
        """Handle LLM response."""
        try:
            # Try to parse JSON
            data = json.loads(content)
            mode = data.get("mode", "chat")
            thought = data.get("thought", "")
            command = data.get("command")
            
            self.log_chat("assistant", thought)
            self.conversation.append({"role": "assistant", "content": thought})
            
            if mode == "shell" and command:
                dangerous = data.get("dangerous", False)
                if dangerous:
                    # Show as ghost command for confirmation
                    self.ghost_command = command
                    self.query_one("#ghost-command", GhostCommandWidget).command = command
                    self.log_exec(f"[yellow]⚠️ Dangerous command suggested: {command}[/yellow]")
                else:
                    # Execute directly
                    await self._execute_command(command)
            
            elif mode == "plan":
                steps = data.get("steps", [])
                self.log_exec(f"[cyan]Plan with {len(steps)} steps:[/cyan]")
                for i, step in enumerate(steps, 1):
                    self.log_exec(f"  {i}. {step.get('description', step.get('command', ''))}")
            
        except json.JSONDecodeError:
            # Not JSON, treat as plain text
            self.log_chat("assistant", content)
            self.conversation.append({"role": "assistant", "content": content})
    
    async def _execute_command(self, command: str) -> None:
        """Execute a shell command."""
        self.log_exec(f"[green]$ {command}[/green]")
        
        if self.shell:
            result = await self.shell.execute(command)
            if result.get("success"):
                output = result.get("output", "")
                if output:
                    self.log_exec(output[:500] + ("..." if len(output) > 500 else ""))
                self.log_exec("[green]✓ Command completed[/green]")
            else:
                self.log_exec(f"[red]✗ {result.get('error', 'Unknown error')}[/red]")
        else:
            # Fallback to subprocess
            import subprocess
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                if result.stdout:
                    self.log_exec(result.stdout[:500])
                if result.stderr:
                    self.log_exec(f"[yellow]{result.stderr[:200]}[/yellow]")
                self.log_exec(f"[{'green' if result.returncode == 0 else 'red'}]Exit: {result.returncode}[/]")
            except subprocess.TimeoutExpired:
                self.log_exec("[red]Command timed out[/red]")
            except Exception as e:
                self.log_exec(f"[red]Error: {e}[/red]")


def main():
    """Run the Astro-OS TUI."""
    app = AstroOS()
    app.run()


if __name__ == "__main__":
    main()
