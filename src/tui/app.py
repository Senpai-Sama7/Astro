#!/usr/bin/env python3
"""
ASTRO Terminal UI - A Claude Code-like conversational interface
Rich, beautiful TUI with full capabilities
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Input, Button, 
    Label, LoadingIndicator, Markdown, Tree, DirectoryTree
)
from textual.binding import Binding
from textual.screen import Screen, ModalScreen
from textual import events
from rich.console import Console
from rich.markdown import Markdown as RichMarkdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text

from src.client.agent import AstroAgent


CSS = """
Screen {
    background: $surface;
}

#app-container {
    height: 100%;
    width: 100%;
}

#chat-container {
    height: 1fr;
    border: solid $primary;
    border-title-color: $primary;
    padding: 0 1;
    margin: 0 1;
}

#messages {
    height: 1fr;
    scrollbar-gutter: stable;
}

.message {
    margin: 1 0;
    padding: 1 2;
}

.user-message {
    background: $primary 20%;
    border-left: thick $primary;
    margin-left: 4;
}

.assistant-message {
    background: $surface;
    border-left: thick $secondary;
}

.system-message {
    background: $warning 15%;
    border-left: thick $warning;
    text-style: italic;
}

.tool-message {
    background: $success 15%;
    border-left: thick $success;
    padding: 0 1;
}

.error-message {
    background: $error 20%;
    border-left: thick $error;
}

.message-header {
    color: $text-muted;
    text-style: bold;
}

.message-content {
    margin-top: 1;
}

#input-container {
    height: auto;
    max-height: 8;
    margin: 1;
    padding: 0 1;
}

#user-input {
    width: 1fr;
    border: tall $primary;
}

#user-input:focus {
    border: tall $secondary;
}

#send-button {
    width: 12;
    margin-left: 1;
}

#status-bar {
    height: 1;
    background: $primary 30%;
    padding: 0 2;
    color: $text;
}

#sidebar {
    width: 30;
    border-right: solid $primary-darken-2;
    display: none;
}

#sidebar.visible {
    display: block;
}

.sidebar-section {
    padding: 1;
    border-bottom: solid $primary-darken-3;
}

.sidebar-title {
    text-style: bold;
    color: $primary;
    margin-bottom: 1;
}

#quick-actions {
    height: auto;
    padding: 1;
}

.quick-btn {
    width: 100%;
    margin: 0 0 1 0;
}

#thinking-indicator {
    height: 3;
    content-align: center middle;
    display: none;
}

#thinking-indicator.visible {
    display: block;
}

WelcomeScreen {
    align: center middle;
}

#welcome-container {
    width: 70;
    height: auto;
    border: round $primary;
    padding: 2 4;
    background: $surface;
}

#welcome-title {
    text-align: center;
    text-style: bold;
    color: $primary;
    margin-bottom: 1;
}

#welcome-subtitle {
    text-align: center;
    color: $text-muted;
    margin-bottom: 2;
}

.welcome-section {
    margin: 1 0;
}

.welcome-heading {
    text-style: bold;
    margin-bottom: 1;
}

HelpScreen {
    align: center middle;
}

#help-container {
    width: 80;
    height: 80%;
    border: round $primary;
    padding: 2;
    background: $surface;
}

#help-content {
    height: 1fr;
}

ConfirmScreen {
    align: center middle;
}

#confirm-dialog {
    width: 60;
    height: auto;
    border: round $warning;
    padding: 2;
    background: $surface;
}

#confirm-title {
    text-style: bold;
    color: $warning;
    margin-bottom: 1;
}

#confirm-buttons {
    margin-top: 2;
    align: center middle;
}

#confirm-buttons Button {
    margin: 0 1;
}
"""


class Message(Static):
    """A chat message widget"""
    
    def __init__(self, content: str, role: str = "assistant", **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.role = role
        
    def compose(self) -> ComposeResult:
        role_labels = {
            "user": "You",
            "assistant": "ASTRO",
            "system": "System",
            "tool": "Tool Result",
            "error": "Error"
        }
        
        role_classes = {
            "user": "user-message",
            "assistant": "assistant-message", 
            "system": "system-message",
            "tool": "tool-message",
            "error": "error-message"
        }
        
        self.add_class("message")
        self.add_class(role_classes.get(self.role, "assistant-message"))
        
        timestamp = datetime.now().strftime("%H:%M")
        yield Static(f"{role_labels.get(self.role, 'ASTRO')} • {timestamp}", classes="message-header")
        yield Static(self.content, classes="message-content")


class WelcomeScreen(ModalScreen):
    """Welcome screen shown on first launch"""
    
    BINDINGS = [
        Binding("enter", "dismiss", "Start"),
        Binding("escape", "dismiss", "Start"),
    ]
    
    def compose(self) -> ComposeResult:
        with Container(id="welcome-container"):
            yield Static("🚀 Welcome to ASTRO", id="welcome-title")
            yield Static("Your AI-Powered Terminal Assistant", id="welcome-subtitle")
            
            with Container(classes="welcome-section"):
                yield Static("Just type what you want to do in plain English:", classes="welcome-heading")
                yield Static('  • "Show me the files in this folder"')
                yield Static('  • "What changed in git?"')
                yield Static('  • "Run the tests"')
                yield Static('  • "Search the web for Python tutorials"')
                yield Static('  • "Explain this code to me"')
            
            with Container(classes="welcome-section"):
                yield Static("Keyboard Shortcuts:", classes="welcome-heading")
                yield Static("  Ctrl+S  Toggle sidebar")
                yield Static("  Ctrl+L  Clear chat")
                yield Static("  Ctrl+H  Show help")
                yield Static("  Ctrl+Q  Quit")
            
            yield Static("\n[Press Enter to start]", id="welcome-subtitle")


class HelpScreen(ModalScreen):
    """Help screen with all commands and capabilities"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]
    
    HELP_TEXT = """
# ASTRO Help

## What Can ASTRO Do?

### 📁 File Operations
- "Show me the files here"
- "Read the contents of config.py"
- "Create a new file called notes.txt"
- "What's in the src folder?"

### 🔀 Git Operations  
- "What's the git status?"
- "Show me what changed"
- "What branch am I on?"

### 🧪 Testing
- "Run the tests"
- "Run pytest with verbose output"

### 🔍 Code Analysis
- "Lint my code"
- "Check for style issues"

### 🌐 Web Search
- "Search for React hooks tutorial"
- "Find Python best practices"

### 🧮 Calculations
- "What's 15% of 230?"
- "Calculate 1024 * 768"

### 💾 Memory
- "Remember that the API key is in .env"
- "What did I ask you to remember?"

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Enter | Send message |
| Ctrl+S | Toggle sidebar |
| Ctrl+L | Clear chat history |
| Ctrl+H | Show this help |
| Ctrl+Q | Quit ASTRO |
| Up/Down | Scroll messages |
| Escape | Close dialogs |

## Tips

- Be conversational! ASTRO understands natural language.
- You can ask follow-up questions.
- If ASTRO asks for confirmation, type "yes" or "no".
- Use the sidebar for quick actions.

[Press Escape or Q to close]
"""
    
    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            with ScrollableContainer(id="help-content"):
                yield Markdown(self.HELP_TEXT)


class ConfirmScreen(ModalScreen[bool]):
    """Confirmation dialog for risky actions"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self.message = message
    
    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog"):
            yield Static("⚠️ Confirmation Required", id="confirm-title")
            yield Static(self.message)
            with Horizontal(id="confirm-buttons"):
                yield Button("Yes, proceed", id="confirm-yes", variant="warning")
                yield Button("No, cancel", id="confirm-no", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")


class AstroTUI(App):
    """Main ASTRO Terminal UI Application"""
    
    TITLE = "ASTRO"
    SUB_TITLE = "AI-Powered Terminal Assistant"
    CSS = CSS
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+s", "toggle_sidebar", "Sidebar", show=True),
        Binding("ctrl+l", "clear_chat", "Clear", show=True),
        Binding("ctrl+h", "show_help", "Help", show=True),
        Binding("escape", "cancel", "Cancel", show=False),
    ]
    
    def __init__(self, api_url: str = "http://localhost:5000"):
        super().__init__()
        self.agent = AstroAgent(api_url=api_url)
        self.history: List[Dict[str, str]] = []
        self.is_processing = False
        self.sidebar_visible = False
        self.first_launch = True
        self._message_task: Optional[asyncio.Task] = None
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="app-container"):
            # Sidebar
            with Container(id="sidebar"):
                with Container(classes="sidebar-section"):
                    yield Static("Quick Actions", classes="sidebar-title")
                    yield Button("📁 List files", classes="quick-btn", id="qa-files")
                    yield Button("🔀 Git status", classes="quick-btn", id="qa-git")
                    yield Button("🧪 Run tests", classes="quick-btn", id="qa-tests")
                    yield Button("🔍 Search web", classes="quick-btn", id="qa-search")
                
                with Container(classes="sidebar-section"):
                    yield Static("Session", classes="sidebar-title")
                    yield Button("🗑️ Clear chat", classes="quick-btn", id="qa-clear")
                    yield Button("❓ Help", classes="quick-btn", id="qa-help")
            
            # Main chat area
            with Container(id="main-area"):
                with Container(id="chat-container"):
                    with ScrollableContainer(id="messages"):
                        yield Static(
                            "👋 Hi! I'm ASTRO, your AI assistant.\n\n"
                            "Just type what you want to do in plain English.\n"
                            "For example: \"Show me the files in this folder\"\n\n"
                            "Press Ctrl+H for help or Ctrl+S to show the sidebar.",
                            classes="message system-message"
                        )
                    
                    with Container(id="thinking-indicator"):
                        yield LoadingIndicator()
                        yield Static("ASTRO is thinking...")
                
                with Horizontal(id="input-container"):
                    yield Input(
                        placeholder="Type what you want to do...",
                        id="user-input"
                    )
                    yield Button("Send", id="send-button", variant="primary")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted"""
        self.query_one("#user-input", Input).focus()
        if self.first_launch:
            self.first_launch = False
            self.push_screen(WelcomeScreen())
    
    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility"""
        sidebar = self.query_one("#sidebar")
        self.sidebar_visible = not self.sidebar_visible
        if self.sidebar_visible:
            sidebar.add_class("visible")
        else:
            sidebar.remove_class("visible")
    
    def action_clear_chat(self) -> None:
        """Clear chat history"""
        messages = self.query_one("#messages", ScrollableContainer)
        messages.remove_children()
        messages.mount(Static(
            "💬 Chat cleared. How can I help you?",
            classes="message system-message"
        ))
        self.history.clear()
    
    def action_show_help(self) -> None:
        """Show help screen"""
        self.push_screen(HelpScreen())
    
    def action_cancel(self) -> None:
        """Cancel current operation"""
        if self.is_processing and self._message_task:
            self._message_task.cancel()
            self.notify("Cancelling operation...", severity="warning")
            self.show_thinking(False)
            self.is_processing = False
            self.query_one("#user-input", Input).focus()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        quick_actions = {
            "qa-files": "List the files in the current directory",
            "qa-git": "Show me the git status",
            "qa-tests": "Run the tests",
            "qa-search": "Search the web for",
            "qa-clear": None,
            "qa-help": None,
        }
        
        if button_id == "send-button":
            await self.send_message()
        elif button_id == "qa-clear":
            self.action_clear_chat()
        elif button_id == "qa-help":
            self.action_show_help()
        elif button_id in quick_actions and quick_actions[button_id]:
            input_widget = self.query_one("#user-input", Input)
            input_widget.value = quick_actions[button_id]
            input_widget.focus()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input"""
        if event.input.id == "user-input":
            await self.send_message()
    
    def add_message(self, content: str, role: str = "assistant") -> None:
        """Add a message to the chat"""
        messages = self.query_one("#messages", ScrollableContainer)
        message = Message(content, role)
        messages.mount(message)
        messages.scroll_end(animate=False)
    
    def show_thinking(self, show: bool = True) -> None:
        """Show/hide thinking indicator"""
        indicator = self.query_one("#thinking-indicator")
        if show:
            indicator.add_class("visible")
        else:
            indicator.remove_class("visible")
    
    async def send_message(self) -> None:
        """Send user message and get response"""
        input_widget = self.query_one("#user-input", Input)
        message = input_widget.value.strip()
        
        if not message or self.is_processing:
            return
        
        input_widget.value = ""
        self.is_processing = True
        
        # Add user message
        self.add_message(message, "user")
        self.history.append({"role": "user", "content": message})
        
        # Show thinking indicator
        self.show_thinking(True)
        
        try:
            # Process with agent
            response = await asyncio.to_thread(
                self.agent.process_message, 
                message
            )
            
            self.show_thinking(False)
            
            # Handle response
            if response.get("requires_approval"):
                confirmed = await self.push_screen_wait(
                    ConfirmScreen(response.get("approval_message", "Proceed with this action?"))
                )
                if confirmed:
                    response = await asyncio.to_thread(
                        self.agent.process_message,
                        "yes"
                    )
                else:
                    response = {"response": "Action cancelled."}
            
            # Show tool execution if any
            if response.get("tool_executed"):
                tool_info = f"🔧 Executed: {response['tool_executed']}"
                if response.get("tool_result"):
                    tool_info += f"\n{response['tool_result']}"
                self.add_message(tool_info, "tool")
            
            # Show response
            assistant_response = response.get("response", "I'm not sure how to help with that.")
            self.add_message(assistant_response, "assistant")
            self.history.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            self.show_thinking(False)
            self.add_message(f"Sorry, something went wrong: {str(e)}", "error")
        
        finally:
            self.is_processing = False
            input_widget.focus()


def main(api_url: str = "http://localhost:5000"):
    """Entry point for the TUI"""
    app = AstroTUI(api_url=api_url)
    app.run()


if __name__ == "__main__":
    main()
