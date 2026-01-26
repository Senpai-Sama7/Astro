#!/usr/bin/env python3
"""
ASTRO Shell - A vibe coding interface with ReAct loop.
No JSON, no endpoints, no session management. Just chat.
"""

import os
import sys
import json
import subprocess
import re
import readline
from pathlib import Path
from typing import Optional
import requests

# Config
API_BASE = os.getenv("ASTRO_API", "http://localhost:5000/api/v1")
SESSION_FILE = Path.home() / ".astro_session"
HISTORY_FILE = Path.home() / ".astro_history"

class AstroShell:
    def __init__(self):
        self.token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.cwd = os.getcwd()
        self.load_session()
        self.setup_readline()
        
    def setup_readline(self):
        """Setup command history."""
        if HISTORY_FILE.exists():
            readline.read_history_file(HISTORY_FILE)
        readline.set_history_length(1000)
    
    def save_history(self):
        readline.write_history_file(HISTORY_FILE)
    
    def load_session(self):
        """Load existing session or create new one."""
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text())
                self.token = data.get("token")
                self.session_id = data.get("session_id")
            except:
                pass
        if not self.token:
            self.authenticate()
    
    def save_session(self):
        SESSION_FILE.write_text(json.dumps({
            "token": self.token,
            "session_id": self.session_id
        }))
    
    def authenticate(self):
        """Get auth token silently."""
        try:
            r = requests.post(f"{API_BASE}/auth/dev-token", 
                json={"userId": os.getenv("USER", "user"), "role": "admin"}, timeout=5)
            if r.ok:
                self.token = r.json().get("token")
                self.save_session()
        except:
            pass  # Offline mode
    
    def chat(self, message: str) -> str:
        """Send message to ARIA."""
        if not self.token:
            return self.react_loop(message)  # Fallback to local ReAct
        try:
            r = requests.post(f"{API_BASE}/aria/chat",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"message": message, "sessionId": self.session_id}, timeout=30)
            if r.ok:
                data = r.json()
                self.session_id = data.get("sessionId", self.session_id)
                self.save_session()
                return data.get("response", "")
        except:
            pass
        return self.react_loop(message)  # Fallback
    
    def react_loop(self, query: str) -> str:
        """
        ReAct Loop: Reason about the query, Act on the environment, Observe results.
        This runs locally when API is unavailable or for system operations.
        """
        thoughts = []
        actions_taken = []
        max_steps = 5
        
        # Analyze intent
        intent = self.analyze_intent(query)
        
        for step in range(max_steps):
            # REASON: What do I need to do?
            thought = self.reason(query, intent, thoughts, actions_taken)
            thoughts.append(thought)
            
            if thought.get("done"):
                break
            
            # ACT: Execute the action
            action = thought.get("action")
            if action:
                result = self.act(action)
                actions_taken.append({"action": action, "result": result})
                
                # OBSERVE: Check if we have enough info
                if self.is_sufficient(query, actions_taken):
                    break
        
        # Generate final response
        return self.synthesize(query, thoughts, actions_taken)
    
    def analyze_intent(self, query: str) -> dict:
        """Determine what the user wants."""
        q = query.lower()
        return {
            "wants_file_read": any(w in q for w in ["read", "show", "cat", "view", "what's in", "contents"]),
            "wants_file_write": any(w in q for w in ["write", "create", "save", "make file"]),
            "wants_list": any(w in q for w in ["list", "ls", "dir", "what files", "show files"]),
            "wants_run": any(w in q for w in ["run", "execute", "start", "launch"]),
            "wants_git": any(w in q for w in ["git", "commit", "push", "pull", "status", "diff"]),
            "wants_search": any(w in q for w in ["find", "search", "grep", "where"]),
            "wants_edit": any(w in q for w in ["edit", "change", "modify", "fix", "update"]),
            "wants_explain": any(w in q for w in ["explain", "what is", "how", "why"]),
            "path_mentioned": self.extract_path(query),
        }
    
    def extract_path(self, query: str) -> Optional[str]:
        """Extract file/directory path from query."""
        # Match quoted paths or common patterns
        patterns = [
            r'"([^"]+)"',
            r"'([^']+)'",
            r'`([^`]+)`',
            r'(\S+\.\w+)',  # file.ext
            r'(~/\S+)',     # ~/path
            r'(\./\S+)',    # ./path
            r'(/\S+)',      # /absolute/path
        ]
        for p in patterns:
            m = re.search(p, query)
            if m:
                return m.group(1)
        return None
    
    def reason(self, query: str, intent: dict, thoughts: list, actions: list) -> dict:
        """Decide next action based on context."""
        # If we have no actions yet, start with reconnaissance
        if not actions:
            if intent["wants_list"] or (not intent["path_mentioned"] and intent["wants_file_read"]):
                return {"thought": "First, let me see what's here", "action": {"type": "shell", "cmd": "ls -la"}}
            if intent["wants_git"]:
                return {"thought": "Checking git status", "action": {"type": "shell", "cmd": "git status"}}
            if intent["wants_search"]:
                pattern = self.extract_search_pattern(query)
                return {"thought": f"Searching for {pattern}", "action": {"type": "shell", "cmd": f"grep -r '{pattern}' . 2>/dev/null | head -20"}}
            if intent["path_mentioned"]:
                path = intent["path_mentioned"]
                if intent["wants_file_read"]:
                    return {"thought": f"Reading {path}", "action": {"type": "read", "path": path}}
                if intent["wants_edit"]:
                    return {"thought": f"First, let me see {path}", "action": {"type": "read", "path": path}}
        
        # If we've done reconnaissance, proceed with main action
        if len(actions) == 1:
            if intent["wants_edit"] and intent["path_mentioned"]:
                return {"thought": "Now I can suggest edits", "done": True}
            if intent["wants_explain"]:
                return {"thought": "I have enough context to explain", "done": True}
        
        # Default: we're done
        return {"thought": "I have enough information", "done": True}
    
    def extract_search_pattern(self, query: str) -> str:
        """Extract search pattern from query."""
        for prefix in ["find ", "search for ", "grep ", "where is "]:
            if prefix in query.lower():
                return query.lower().split(prefix)[1].split()[0]
        return query.split()[-1]
    
    def act(self, action: dict) -> str:
        """Execute an action and return result."""
        action_type = action.get("type")
        
        if action_type == "shell":
            return self.run_shell(action["cmd"])
        elif action_type == "read":
            return self.read_file(action["path"])
        elif action_type == "write":
            return self.write_file(action["path"], action["content"])
        elif action_type == "search":
            return self.run_shell(f"grep -r '{action['pattern']}' . 2>/dev/null | head -20")
        
        return "Unknown action"
    
    def run_shell(self, cmd: str) -> str:
        """Execute shell command safely."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                                   timeout=30, cwd=self.cwd)
            output = result.stdout or result.stderr
            return output[:2000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "(command timed out)"
        except Exception as e:
            return f"(error: {e})"
    
    def read_file(self, path: str) -> str:
        """Read file contents."""
        try:
            p = Path(path).expanduser()
            if not p.is_absolute():
                p = Path(self.cwd) / p
            content = p.read_text()
            return content[:3000] if len(content) > 3000 else content
        except Exception as e:
            return f"(cannot read: {e})"
    
    def write_file(self, path: str, content: str) -> str:
        """Write file contents."""
        try:
            p = Path(path).expanduser()
            if not p.is_absolute():
                p = Path(self.cwd) / p
            p.write_text(content)
            return f"Written to {p}"
        except Exception as e:
            return f"(cannot write: {e})"
    
    def is_sufficient(self, query: str, actions: list) -> bool:
        """Check if we have enough info to answer."""
        return len(actions) >= 2
    
    def synthesize(self, query: str, thoughts: list, actions: list) -> str:
        """Generate final response from gathered info."""
        parts = []
        
        for t in thoughts:
            if t.get("thought"):
                parts.append(f"💭 {t['thought']}")
        
        for a in actions:
            result = a["result"]
            if len(result) > 500:
                result = result[:500] + "..."
            parts.append(f"📋 {result}")
        
        return "\n".join(parts) if parts else "I'm not sure how to help with that."
    
    def handle_builtin(self, cmd: str) -> Optional[str]:
        """Handle shell built-in commands."""
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
            return None
        
        if builtin == "help":
            return """
🚀 ASTRO Shell - Just chat naturally!

Examples:
  "what files are here?"
  "show me the contents of main.py"
  "find all TODO comments"
  "what's the git status?"
  "run the tests"
  
Or use regular shell commands:
  ls, cd, pwd, cat, grep, git, etc.

Built-ins: cd, pwd, clear, help, exit
"""
        
        return None
    
    def is_shell_command(self, cmd: str) -> bool:
        """Check if input looks like a direct shell command."""
        shell_cmds = ["ls", "cat", "grep", "find", "git", "npm", "python", "node", 
                     "make", "cargo", "go", "docker", "kubectl", "curl", "wget",
                     "head", "tail", "less", "more", "vim", "nano", "code"]
        first_word = cmd.strip().split()[0] if cmd.strip() else ""
        return first_word in shell_cmds or cmd.startswith("./") or cmd.startswith("/")
    
    def prompt(self) -> str:
        """Generate prompt string."""
        cwd_short = self.cwd.replace(str(Path.home()), "~")
        if len(cwd_short) > 30:
            cwd_short = "..." + cwd_short[-27:]
        status = "🟢" if self.token else "🔴"
        return f"{status} {cwd_short} ❯ "
    
    def run(self):
        """Main REPL loop."""
        print("🚀 ASTRO Shell - Just chat naturally (type 'help' for examples)")
        print(f"📂 {self.cwd}\n")
        
        while True:
            try:
                user_input = input(self.prompt()).strip()
                if not user_input:
                    continue
                
                # Check for built-ins first
                builtin_result = self.handle_builtin(user_input)
                if builtin_result is not None:
                    if builtin_result:
                        print(builtin_result)
                    continue
                
                # Direct shell command?
                if self.is_shell_command(user_input):
                    result = self.run_shell(user_input)
                    print(result)
                    continue
                
                # Natural language -> ReAct loop
                response = self.chat(user_input)
                print(f"\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n(Use 'exit' to quit)")
            except EOFError:
                self.save_history()
                print("\n👋 Bye!")
                break

if __name__ == "__main__":
    shell = AstroShell()
    shell.run()
