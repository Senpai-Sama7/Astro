#!/usr/bin/env python3
"""
Astro-OS: Production-grade Autonomous TUI Agent for Lubuntu/Kali Linux.

A 3-panel dashboard with streaming chat, live execution logs, and ghost commands.
"""

import os
import sys
import json
import asyncio
import platform
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, RichLog, Markdown
from textual.binding import Binding
from textual.message import Message
from textual import work
from rich.syntax import Syntax
from rich.markdown import Markdown as RichMarkdown

# Local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from astro_os.tools import ShellTool, BrowserTool
from astro_os.memory import Memory

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


class ChatMessage(Static):
    """A chat message widget."""
    
    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.content = content
    
    def compose(self) -> ComposeResult:
        prefix = "🧑 You" if self.role == "user" else "🤖 Astro"
        color = "green" if self.role == "user" else "cyan"
        yield Static(f"[bold {color}]{prefix}[/]")
        yield Markdown(self.content)


class GhostCommand(Message):
    """Message for ghost command suggestion."""
    def __init__(self, command: str):
        super().__init__()
        self.command = command


class AstroOS(App):
    """Astro-OS TUI Application."""
    
    CSS = """
    #main-container {
        layout: horizontal;
    }
    #chat-panel {
        width: 65%;
        border: solid green;
        padding: 1;
    }
    #sidebar {
        width: 35%;
        border: solid cyan;
        padding: 1;
    }
    #chat-log {
        height: 1fr;
        scrollbar-gutter: stable;
    }
    #exec-log {
        height: 1fr;
        scrollbar-gutter: stable;
    }
    #input-container {
        height: auto;
        dock: bottom;
    }
    #user-input {
        width: 100%;
    }
    .message {
        margin: 1 0;
        padding: 1;
        background: $surface;
    }
    .user-message {
        border-left: thick green;
    }
    .assistant-message {
        border-left: thick cyan;
    }
    Footer {
        background: $primary-darken-2;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "interrupt", "Interrupt", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_logs", "Clear Logs", show=True),
        Binding("ctrl+m", "toggle_mode", "Toggle Mode", show=True),
        Binding("ctrl+p", "index_project", "Index Project", show=True),
        Binding("escape", "cancel_ghost", "Cancel Ghost", show=False),
        Binding("enter", "submit", "Submit", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.memory = Memory()
        self.shell = ShellTool(cwd=self.memory.state.cwd, log_callback=self.log_exec)
        self.browser = BrowserTool(log_callback=self.log_exec, vision_callback=self.vision_analyze)
        self.mode = self.memory.state.mode
        self.running_task: Optional[asyncio.Task] = None
        self.ghost_command: Optional[str] = None
        self.os_info = self._detect_os()
        
        # LLM client
        self.llm_client = None
        self.llm_provider = None
        self._init_llm()
    
    def _detect_os(self) -> str:
        if platform.system() == "Linux":
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=")[1].strip().strip('"')
            except:
                pass
        return f"{platform.system()} {platform.release()}"
    
    def _init_llm(self):
        if HAS_OPENAI and os.environ.get("OPENAI_API_KEY"):
            self.llm_client = AsyncOpenAI()
            self.llm_provider = "openai"
            self.model = os.environ.get("ASTRO_MODEL", "gpt-4o-mini")
        elif HAS_ANTHROPIC and os.environ.get("ANTHROPIC_API_KEY"):
            self.llm_client = anthropic.AsyncAnthropic()
            self.llm_provider = "anthropic"
            self.model = os.environ.get("ASTRO_MODEL", "claude-3-haiku-20240307")
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Vertical(id="chat-panel"):
                yield Static("[bold green]💬 Chat[/]", id="chat-title")
                yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
                with Container(id="input-container"):
                    yield Input(placeholder="Ask Astro anything...", id="user-input")
            with Vertical(id="sidebar"):
                yield Static("[bold cyan]⚡ Live Execution[/]", id="exec-title")
                yield RichLog(id="exec-log", highlight=True, markup=True, auto_scroll=True)
        yield Footer()
    
    def on_mount(self):
        self.title = "Astro-OS"
        self.sub_title = f"Mode: {self.mode.upper()} | Session: {self.memory.state.session_id[:8]} | CWD: {self.shell.cwd}"
        
        # Welcome message
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(f"[bold cyan]🚀 Astro-OS initialized[/]")
        chat_log.write(f"[dim]OS: {self.os_info}[/]")
        chat_log.write(f"[dim]LLM: {self.llm_provider or 'None'}/{self.model if self.llm_client else 'N/A'}[/]")
        chat_log.write(f"[dim]Type a command or question. Ctrl+C to interrupt, Ctrl+Q to quit.[/]\n")
        
        if not self.llm_client:
            chat_log.write("[bold red]⚠️ No LLM configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY[/]")
        
        # Focus input
        self.query_one("#user-input", Input).focus()
    
    async def log_exec(self, msg: str):
        """Log to execution panel."""
        exec_log = self.query_one("#exec-log", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        exec_log.write(f"[dim]{timestamp}[/] {msg}")
    
    async def log_chat(self, role: str, content: str):
        """Log to chat panel."""
        chat_log = self.query_one("#chat-log", RichLog)
        if role == "user":
            chat_log.write(f"\n[bold green]🧑 You:[/] {content}")
        else:
            chat_log.write(f"\n[bold cyan]🤖 Astro:[/]")
            # Try to render as markdown
            try:
                chat_log.write(RichMarkdown(content))
            except:
                chat_log.write(content)
    
    def update_status(self):
        """Update footer status."""
        self.sub_title = f"Mode: {self.mode.upper()} | Session: {self.memory.state.session_id[:8]} | CWD: {self.shell.cwd}"
    
    async def vision_analyze(self, screenshot_b64: str, prompt: str) -> str:
        """Analyze screenshot with vision model."""
        if not self.llm_client or self.llm_provider != "openai":
            return '{"found": false, "reason": "Vision not available"}'
        
        try:
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
                    ]
                }],
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f'{{"found": false, "reason": "{str(e)}"}}'
    
    async def call_llm(self, messages: list) -> Optional[str]:
        """Call LLM API."""
        if not self.llm_client:
            return None
        
        try:
            if self.llm_provider == "openai":
                response = await self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            elif self.llm_provider == "anthropic":
                system = messages[0]["content"] if messages[0]["role"] == "system" else ""
                msgs = [m for m in messages if m["role"] != "system"]
                response = await self.llm_client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=system,
                    messages=msgs
                )
                return response.content[0].text
        except Exception as e:
            await self.log_exec(f"[red]LLM Error: {e}[/]")
            return None
    
    def set_ghost_command(self, command: str):
        """Set ghost command in input."""
        self.ghost_command = command
        input_widget = self.query_one("#user-input", Input)
        input_widget.value = command
        input_widget.cursor_position = len(command)
        self.query_one("#chat-log", RichLog).write(f"[dim]👻 Ghost command ready. Press Enter to execute or Escape to cancel.[/]")
    
    async def process_response(self, response: str):
        """Process LLM response and execute actions."""
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            await self.log_chat("assistant", response)
            return
        
        thought = data.get("thought", "")
        mode = data.get("mode", "chat")
        
        # Show thought
        if thought:
            await self.log_chat("assistant", f"💭 {thought}")
        
        # Handle different modes
        if mode == "chat" or data.get("command") is None:
            return
        
        elif mode == "shell":
            command = data.get("command")
            dangerous = data.get("dangerous", False)
            
            if dangerous:
                await self.log_chat("assistant", f"⚠️ **Dangerous command**: `{command}`")
                self.set_ghost_command(command)
            else:
                # Set as ghost command for confirmation
                self.set_ghost_command(command)
        
        elif mode == "web":
            action = data.get("action")
            target = data.get("target")
            value = data.get("value", "")
            
            if not self.browser.page:
                await self.browser.start(headless=True)
            
            if action == "navigate":
                result = await self.browser.navigate(target)
            elif action == "click":
                result = await self.browser.click(target)
            elif action == "type":
                result = await self.browser.type_text(target, value)
            
            # Feed result back
            self.memory.add_message("system", f"Browser {action} result: {result.success}")
        
        elif mode == "plan":
            steps = data.get("steps", [])
            await self.log_chat("assistant", f"📋 **Plan with {len(steps)} steps:**")
            for i, step in enumerate(steps, 1):
                await self.log_chat("assistant", f"  {i}. {step.get('description', step.get('command', ''))}")
            
            # Set first step as ghost command
            if steps:
                first = steps[0]
                self.set_ghost_command(first.get("command", ""))
    
    @work(exclusive=True)
    async def run_agent(self, user_input: str):
        """Run agent task."""
        await self.log_chat("user", user_input)
        self.memory.add_message("user", user_input)
        
        # Build context
        context = self.memory.build_context_prompt()
        system_prompt = SYSTEM_PROMPT.format(os_info=self.os_info, context=context)
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        for msg in self.memory.get_conversation(limit=10):
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        await self.log_exec("[cyan]Thinking...[/]")
        response = await self.call_llm(messages)
        
        if response:
            self.memory.add_message("assistant", response)
            await self.process_response(response)
        else:
            await self.log_chat("assistant", "Sorry, I couldn't process that request.")
    
    @work(exclusive=True)
    async def execute_command(self, command: str):
        """Execute a shell command."""
        self.memory.add_command(command)
        result = await self.shell.execute(command)
        
        # Update CWD
        self.memory.set_cwd(self.shell.cwd)
        self.update_status()
        
        # Show result in chat
        if result.stdout:
            await self.log_chat("assistant", f"```\n{result.stdout[:2000]}\n```")
        if result.stderr:
            await self.log_chat("assistant", f"[red]{result.stderr[:500]}[/]")
        
        # If failed with suggestion, offer fix
        if result.exit_code != 0 and result.suggested_fix:
            await self.log_chat("assistant", f"💡 Suggested fix: `{result.suggested_fix}`")
            self.set_ghost_command(result.suggested_fix)
        
        # Feed result back to LLM for continuation
        self.memory.add_message("system", 
            f"Command `{command}` exited with code {result.exit_code}.\n"
            f"stdout: {result.stdout[:1000]}\nstderr: {result.stderr[:500]}")
    
    async def on_input_submitted(self, event: Input.Submitted):
        """Handle input submission."""
        value = event.value.strip()
        if not value:
            return
        
        event.input.value = ""
        self.ghost_command = None
        
        # Check if it's a direct command (starts with !)
        if value.startswith("!"):
            await self.execute_command(value[1:])
        # Check if it's the ghost command being confirmed
        elif self.ghost_command and value == self.ghost_command:
            await self.execute_command(value)
        else:
            # Send to agent
            self.run_agent(value)
    
    def action_interrupt(self):
        """Interrupt running task."""
        if self.running_task and not self.running_task.done():
            self.running_task.cancel()
            self.query_one("#exec-log", RichLog).write("[yellow]⚠️ Task interrupted[/]")
    
    def action_clear_logs(self):
        """Clear execution logs."""
        self.query_one("#exec-log", RichLog).clear()
    
    def action_toggle_mode(self):
        """Toggle between shell and web mode."""
        self.mode = "web" if self.mode == "shell" else "shell"
        self.memory.set_mode(self.mode)
        self.update_status()
        self.query_one("#exec-log", RichLog).write(f"[cyan]Mode: {self.mode.upper()}[/]")
    
    def action_cancel_ghost(self):
        """Cancel ghost command."""
        if self.ghost_command:
            self.ghost_command = None
            self.query_one("#user-input", Input).value = ""
            self.query_one("#chat-log", RichLog).write("[dim]Ghost command cancelled[/]")
    
    @work
    async def action_index_project(self):
        """Index current project."""
        await self.log_exec("[cyan]Indexing project...[/]")
        ctx = self.memory.index_project(self.shell.cwd)
        await self.log_exec(f"[green]Indexed: {ctx.name}[/]")
        await self.log_exec(f"[dim]Languages: {', '.join(ctx.languages)}[/]")
        await self.log_exec(f"[dim]Files: {len(ctx.structure)}[/]")


def main():
    """Entry point."""
    app = AstroOS()
    app.run()


if __name__ == "__main__":
    main()
