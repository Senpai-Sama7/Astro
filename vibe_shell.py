#!/usr/bin/env python3
"""
ASTRO Vibe Shell - LLM-powered ReAct orchestrator.
Bridges natural language and your local Linux environment.
"""

import os
import sys
import json
import subprocess
import re
import readline
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import requests

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Config
API_BASE = os.getenv("ASTRO_API", "http://localhost:5000/api/v1")
SESSION_FILE = Path.home() / ".astro_session"
HISTORY_FILE = Path.home() / ".astro_history"

SYSTEM_PROMPT = """You are ASTRO, an AI assistant with direct access to the user's Linux environment.
You can execute shell commands, read/write files, and help with coding tasks.

When the user asks something, think step by step:
1. THOUGHT: What do I need to do? What information do I need?
2. ACTION: Execute a tool to gather info or make changes
3. OBSERVATION: Review the result
4. Repeat until you can give a final ANSWER

Available tools:
- shell(cmd): Execute a shell command
- read_file(path): Read file contents
- write_file(path, content): Write to a file
- search(pattern, path): Search for pattern in files

Respond in this format:
THOUGHT: <your reasoning>
ACTION: <tool_name>(<args>)

Or when done:
THOUGHT: <final reasoning>
ANSWER: <your response to the user>

Be concise. Execute commands to verify things rather than guessing."""

@dataclass
class Action:
    tool: str
    args: Dict[str, Any]
    
@dataclass  
class Step:
    thought: str
    action: Optional[Action] = None
    observation: Optional[str] = None
    answer: Optional[str] = None

class VibeShell:
    def __init__(self):
        self.cwd = os.getcwd()
        self.token: Optional[str] = None
        self.history: List[Dict] = []
        self.llm_client = self._init_llm()
        self.load_session()
        self.setup_readline()
        
    def _init_llm(self):
        """Initialize LLM client."""
        if HAS_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY"):
            return ("anthropic", Anthropic())
        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            return ("openai", OpenAI())
        return None
    
    def setup_readline(self):
        if HISTORY_FILE.exists():
            readline.read_history_file(HISTORY_FILE)
        readline.set_history_length(1000)
    
    def save_history(self):
        readline.write_history_file(HISTORY_FILE)
    
    def load_session(self):
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text())
                self.token = data.get("token")
            except:
                pass
        if not self.token:
            self._authenticate()
    
    def _authenticate(self):
        try:
            r = requests.post(f"{API_BASE}/auth/dev-token",
                json={"userId": os.getenv("USER", "user"), "role": "admin"}, timeout=5)
            if r.ok:
                self.token = r.json().get("token")
                SESSION_FILE.write_text(json.dumps({"token": self.token}))
        except:
            pass

    # ==================== TOOLS ====================
    
    def tool_shell(self, cmd: str) -> str:
        """Execute shell command."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                   timeout=30, cwd=self.cwd)
            output = (result.stdout + result.stderr).strip()
            return output[:4000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "(timed out after 30s)"
        except Exception as e:
            return f"(error: {e})"
    
    def tool_read_file(self, path: str) -> str:
        """Read file contents."""
        try:
            p = Path(path).expanduser()
            if not p.is_absolute():
                p = Path(self.cwd) / p
            content = p.read_text()
            if len(content) > 4000:
                return content[:4000] + f"\n... (truncated, {len(content)} total chars)"
            return content
        except Exception as e:
            return f"(error reading {path}: {e})"
    
    def tool_write_file(self, path: str, content: str) -> str:
        """Write file contents."""
        try:
            p = Path(path).expanduser()
            if not p.is_absolute():
                p = Path(self.cwd) / p
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return f"✓ Written {len(content)} chars to {p}"
        except Exception as e:
            return f"(error writing {path}: {e})"
    
    def tool_search(self, pattern: str, path: str = ".") -> str:
        """Search for pattern in files."""
        cmd = f"grep -rn '{pattern}' {path} 2>/dev/null | head -30"
        return self.tool_shell(cmd)
    
    def execute_action(self, action: Action) -> str:
        """Execute a tool action."""
        tool_map = {
            "shell": lambda a: self.tool_shell(a.get("cmd", "")),
            "read_file": lambda a: self.tool_read_file(a.get("path", "")),
            "write_file": lambda a: self.tool_write_file(a.get("path", ""), a.get("content", "")),
            "search": lambda a: self.tool_search(a.get("pattern", ""), a.get("path", ".")),
        }
        handler = tool_map.get(action.tool)
        if handler:
            return handler(action.args)
        return f"(unknown tool: {action.tool})"

    # ==================== ReAct LOOP ====================
    
    def parse_llm_response(self, text: str) -> Step:
        """Parse LLM response into a Step."""
        step = Step(thought="")
        
        # Extract THOUGHT
        thought_match = re.search(r'THOUGHT:\s*(.+?)(?=ACTION:|ANSWER:|$)', text, re.DOTALL)
        if thought_match:
            step.thought = thought_match.group(1).strip()
        
        # Extract ACTION
        action_match = re.search(r'ACTION:\s*(\w+)\((.+?)\)', text, re.DOTALL)
        if action_match:
            tool = action_match.group(1)
            args_str = action_match.group(2).strip()
            # Parse args - handle both positional and keyword
            args = {}
            if tool == "shell":
                args["cmd"] = args_str.strip('"\'')
            elif tool == "read_file":
                args["path"] = args_str.strip('"\'')
            elif tool == "write_file":
                # write_file("path", "content")
                parts = re.match(r'"([^"]+)"\s*,\s*"(.+)"', args_str, re.DOTALL)
                if parts:
                    args["path"] = parts.group(1)
                    args["content"] = parts.group(2)
            elif tool == "search":
                parts = args_str.split(",", 1)
                args["pattern"] = parts[0].strip().strip('"\'')
                if len(parts) > 1:
                    args["path"] = parts[1].strip().strip('"\'')
            step.action = Action(tool=tool, args=args)
        
        # Extract ANSWER
        answer_match = re.search(r'ANSWER:\s*(.+?)$', text, re.DOTALL)
        if answer_match:
            step.answer = answer_match.group(1).strip()
        
        return step
    
    def call_llm(self, messages: List[Dict]) -> str:
        """Call LLM API."""
        if not self.llm_client:
            return "ANSWER: LLM not configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY."
        
        provider, client = self.llm_client
        
        try:
            if provider == "anthropic":
                # Extract system message
                system = next((m["content"] for m in messages if m["role"] == "system"), "")
                user_msgs = [m for m in messages if m["role"] != "system"]
                
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    system=system,
                    messages=user_msgs
                )
                return response.content[0].text
            
            elif provider == "openai":
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=2000
                )
                return response.choices[0].message.content
        
        except Exception as e:
            return f"ANSWER: LLM error: {e}"
        
        return "ANSWER: Unknown LLM provider"
    
    def react(self, user_input: str) -> str:
        """Run ReAct loop for user query."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Current directory: {self.cwd}\n\nUser: {user_input}"}
        ]
        
        steps: List[Step] = []
        max_steps = 6
        
        for i in range(max_steps):
            # Get LLM response
            response = self.call_llm(messages)
            step = self.parse_llm_response(response)
            steps.append(step)
            
            # Print thought process
            if step.thought:
                print(f"💭 {step.thought}")
            
            # If we have an answer, we're done
            if step.answer:
                return step.answer
            
            # Execute action if present
            if step.action:
                print(f"⚡ {step.action.tool}({json.dumps(step.action.args)[:60]}...)")
                observation = self.execute_action(step.action)
                step.observation = observation
                
                # Show truncated observation
                obs_preview = observation[:200] + "..." if len(observation) > 200 else observation
                print(f"📋 {obs_preview}")
                
                # Add to conversation
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"OBSERVATION: {observation}"})
            else:
                # No action and no answer - ask for clarification
                return "I'm not sure what to do. Can you be more specific?"
        
        return "I took too many steps without reaching a conclusion. Please try a simpler request."

    # ==================== SHELL INTERFACE ====================
    
    def handle_builtin(self, cmd: str) -> Optional[str]:
        """Handle built-in commands."""
        parts = cmd.strip().split()
        if not parts:
            return None
        
        builtin = parts[0]
        
        if builtin == "cd":
            path = parts[1] if len(parts) > 1 else str(Path.home())
            try:
                new_path = Path(path).expanduser()
                if not new_path.is_absolute():
                    new_path = Path(self.cwd) / new_path
                new_path = new_path.resolve()
                if new_path.is_dir():
                    self.cwd = str(new_path)
                    os.chdir(self.cwd)
                    return f"📂 {self.cwd}"
                return f"Not a directory: {path}"
            except Exception as e:
                return str(e)
        
        if builtin == "pwd":
            return self.cwd
        
        if builtin in ["exit", "quit", "q"]:
            self.save_history()
            print("\n👋 Bye!")
            sys.exit(0)
        
        if builtin == "clear":
            os.system("clear")
            return ""
        
        if builtin == "help":
            return """
🚀 ASTRO Vibe Shell - Chat naturally with your system

Just describe what you want:
  "what's in this directory?"
  "show me the main function in app.py"
  "find all files with TODO comments"
  "create a hello world script"
  "what's the git status?"
  "run the tests and tell me what failed"

The AI will reason through your request, execute commands,
read files, and give you a helpful response.

Built-ins: cd, pwd, clear, help, exit
Direct commands: ls, git, npm, etc. (executed directly)
"""
        
        return None
    
    def is_direct_command(self, cmd: str) -> bool:
        """Check if input is a direct shell command."""
        direct_cmds = ["ls", "cat", "grep", "find", "git", "npm", "python", "node",
                      "make", "cargo", "go", "docker", "kubectl", "curl", "wget",
                      "head", "tail", "less", "vim", "nano", "code", "tree", "ps",
                      "top", "htop", "df", "du", "chmod", "chown", "mkdir", "rm",
                      "cp", "mv", "touch", "echo", "which", "man"]
        first = cmd.strip().split()[0] if cmd.strip() else ""
        return first in direct_cmds or cmd.startswith("./") or cmd.startswith("/")
    
    def prompt(self) -> str:
        cwd_short = self.cwd.replace(str(Path.home()), "~")
        if len(cwd_short) > 35:
            cwd_short = "..." + cwd_short[-32:]
        llm_status = "🧠" if self.llm_client else "💤"
        return f"{llm_status} {cwd_short} ❯ "
    
    def run(self):
        """Main REPL."""
        llm_name = self.llm_client[0] if self.llm_client else "none"
        print(f"🚀 ASTRO Vibe Shell (LLM: {llm_name})")
        print(f"📂 {self.cwd}")
        print("Type naturally or 'help' for examples\n")
        
        while True:
            try:
                user_input = input(self.prompt()).strip()
                if not user_input:
                    continue
                
                # Built-in?
                result = self.handle_builtin(user_input)
                if result is not None:
                    if result:
                        print(result)
                    continue
                
                # Direct shell command?
                if self.is_direct_command(user_input):
                    print(self.tool_shell(user_input))
                    continue
                
                # Natural language -> ReAct
                print()  # Spacing
                response = self.react(user_input)
                print(f"\n✨ {response}\n")
                
            except KeyboardInterrupt:
                print("\n(Ctrl+C - use 'exit' to quit)")
            except EOFError:
                self.save_history()
                print("\n👋 Bye!")
                break

if __name__ == "__main__":
    shell = VibeShell()
    shell.run()
