#!/usr/bin/env python3
"""
ASTRO Shell - Local ReAct implementation (safe, rule-based).

This file provides:
- Session handling (save/load token + session_id)
- Chat(endpoint) fallback to a local ReAct loop when API is unavailable
- A simple, deterministic ReAct loop: analyze_intent -> reason -> act -> observe -> synthesize
- Robust exception handling and logging
- Input validation and sanitization

Example usage:
    shell = AstroShell()
    response = shell.chat("show me the contents of README.md")
    print(response)
"""

from __future__ import annotations

import json
import logging
import os
import re
import readline
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Basic config
API_BASE = os.getenv("ASTRO_API", "http://localhost:5000/api/v1")
SESSION_FILE = Path.home() / ".astro_session"
HISTORY_FILE = Path.home() / ".astro_history"

# Constants
DEFAULT_TIMEOUT = 30
MAX_OUTPUT_LENGTH = 4000
MAX_STEPS = 5


# Configure logger
def _setup_logger() -> logging.Logger:
    """Setup and configure the astro_shell logger."""
    logger = logging.getLogger("astro_shell")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


logger = _setup_logger()


class AstroShellError(Exception):
    """Base exception for AstroShell errors."""
    pass


class AuthenticationError(AstroShellError):
    """Raised when authentication fails."""
    pass


class ToolExecutionError(AstroShellError):
    """Raised when a tool execution fails."""
    pass


class ValidationError(AstroShellError):
    """Raised when input validation fails."""
    pass


class AstroShell:
    """
    ASTRO Shell - Local ReAct implementation with API fallback.
    
    This class provides a command-line interface that can either communicate
    with a remote API or use a local ReAct loop for processing user queries.
    
    Attributes:
        token: Authentication token for API access
        session_id: Current session identifier
        cwd: Current working directory
    """

    def __init__(self) -> None:
        """Initialize the AstroShell instance."""
        self.token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.cwd = Path.cwd()
        self.load_session()
        self.setup_readline()

    # -----------------------
    # Readline / Session utils
    # -----------------------
    def setup_readline(self) -> None:
        """
        Setup readline with history file support.
        
        Loads previous command history if available.
        """
        try:
            if HISTORY_FILE.exists():
                readline.read_history_file(str(HISTORY_FILE))
        except (OSError, IOError) as e:
            # Non-fatal - history file may not exist or be readable
            logger.debug("Failed to read history file: %s", e)
        except Exception as e:
            logger.debug("Unexpected error reading history file: %s", e)
        
        try:
            readline.set_history_length(1000)
        except Exception as e:
            logger.debug("Failed to set history length: %s", e)

    def save_history(self) -> None:
        """
        Save command history to file.
        
        Persists current session's command history for future sessions.
        """
        try:
            readline.write_history_file(str(HISTORY_FILE))
        except (OSError, IOError) as e:
            logger.debug("Failed to write history file: %s", e)
        except Exception as e:
            logger.debug("Unexpected error writing history file: %s", e)

    def load_session(self) -> None:
        """
        Load existing session or attempt to authenticate.
        
        Attempts to load token and session_id from the session file.
        If no valid token exists, triggers authentication.
        """
        try:
            if SESSION_FILE.exists():
                content = SESSION_FILE.read_text(encoding="utf-8")
                data = json.loads(content)
                self.token = data.get("token")
                self.session_id = data.get("session_id")
        except json.JSONDecodeError as e:
            logger.debug("Failed to parse session file: %s", e)
        except (OSError, IOError) as e:
            logger.debug("Failed to load session file: %s", e)
        except Exception as e:
            logger.debug("Unexpected error loading session: %s", e)

        if not self.token:
            self.authenticate()

    def save_session(self) -> None:
        """
        Save current session to file.
        
        Persists token and session_id for future sessions.
        """
        try:
            session_data = {
                "token": self.token,
                "session_id": self.session_id
            }
            SESSION_FILE.write_text(
                json.dumps(session_data, indent=2),
                encoding="utf-8"
            )
        except (OSError, IOError) as e:
            logger.debug("Failed to save session file: %s", e)
        except Exception as e:
            logger.debug("Unexpected error saving session: %s", e)

    def authenticate(self, timeout: int = 5, max_retries: int = 2) -> None:
        """
        Try to obtain a dev token silently (best-effort).
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Raises:
            AuthenticationError: If all retry attempts fail (logged but not raised)
        """
        for attempt in range(max_retries):
            try:
                r = requests.post(
                    f"{API_BASE}/auth/dev-token",
                    json={"userId": os.getenv("USER", "user"), "role": "admin"},
                    timeout=timeout,
                )
                if r.ok:
                    data = r.json()
                    self.token = data.get("token")
                    self.session_id = data.get("sessionId", self.session_id)
                    self.save_session()
                    logger.info("Authenticated with remote ARIA")
                    return
                else:
                    logger.debug("Auth request returned non-ok status: %d", r.status_code)
            except requests.exceptions.Timeout:
                logger.debug("Authentication attempt %d timed out", attempt + 1)
            except requests.exceptions.ConnectionError as e:
                logger.debug("Authentication connection error (attempt %d): %s", attempt + 1, e)
            except requests.exceptions.RequestException as e:
                logger.debug("Authentication request error (attempt %d): %s", attempt + 1, e)
            except Exception as e:
                logger.debug("Authentication unexpected error (attempt %d): %s", attempt + 1, e)
        
        # Silent fallback to offline mode; keep local ReAct
        logger.debug("Authentication failed after %d attempts (offline mode)", max_retries)

    # -----------------------
    # API chat wrapper
    # -----------------------
    def chat(self, message: str) -> str:
        """
        Send message to remote ARIA. If remote is unavailable or authentication missing,
        use the local ReAct loop as a fallback.
        
        Args:
            message: The user's message/query
            
        Returns:
            Response string from either the API or local ReAct loop
            
        Raises:
            ValidationError: If message is empty or invalid
        """
        # Input validation
        if not isinstance(message, str):
            raise ValidationError(f"Message must be a string, got {type(message).__name__}")
        
        message = message.strip()
        if not message:
            raise ValidationError("Message cannot be empty")
        
        if not self.token:
            logger.info("No token available; running local ReAct loop as fallback")
            return self.react_loop(message)

        try:
            r = requests.post(
                f"{API_BASE}/aria/chat",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"message": message, "sessionId": self.session_id},
                timeout=DEFAULT_TIMEOUT,
            )
            if r.ok:
                data = r.json()
                self.session_id = data.get("sessionId", self.session_id)
                self.save_session()
                return data.get("response", "")
            else:
                logger.debug("Remote chat returned non-ok (status %d); falling back locally", r.status_code)
        except requests.exceptions.Timeout:
            logger.debug("Remote chat timed out; falling back locally")
        except requests.exceptions.ConnectionError as e:
            logger.debug("Remote chat connection error; falling back locally: %s", e)
        except requests.exceptions.RequestException as e:
            logger.debug("Remote chat request error; falling back locally: %s", e)
        except Exception as e:
            logger.debug("Remote chat unexpected error; falling back locally: %s", e)

        return self.react_loop(message)

    # -----------------------
    # ReAct loop components
    # -----------------------
    def react_loop(self, query: str, max_steps: int = MAX_STEPS) -> str:
        """
        Local ReAct loop (deterministic, rule-based).
        
        Flow: analyze_intent -> reason -> act -> observe -> repeat -> synthesize
        
        Args:
            query: The user's query string
            max_steps: Maximum number of reasoning steps before synthesis
            
        Returns:
            Synthesized response string
            
        Example:
            >>> shell = AstroShell()
            >>> result = shell.react_loop("show me README.md")
            >>> print(result)
        """
        thoughts: List[Dict[str, Any]] = []
        actions_taken: List[Dict[str, Any]] = []

        intent = self.analyze_intent(query)
        logger.debug("Intent: %s", intent)

        for step in range(max_steps):
            thought = self.reason(query, intent, thoughts, actions_taken)
            thoughts.append(thought)
            logger.debug("Thought %d: %s", step + 1, thought.get("thought"))

            if thought.get("done"):
                logger.debug("Thought indicates done")
                break

            action = thought.get("action")
            if action:
                result = self.act(action)
                actions_taken.append({"action": action, "result": result})
                logger.debug("Action result: %s", repr(result))

                if self.is_sufficient(query, actions_taken):
                    logger.debug("Sufficiency reached; breaking loop")
                    break

        return self.synthesize(query, thoughts, actions_taken)

    def analyze_intent(self, query: str) -> Dict[str, Any]:
        """
        Rule-based intent analysis (fast, local).
        
        Analyzes the user query to determine intent flags that downstream
        reasoning can use to decide on appropriate actions.
        
        Args:
            query: The user's query string
            
        Returns:
            Dictionary of intent flags including:
                - wants_shell: True if query starts with !
                - wants_file_read: True if query contains file read keywords
                - wants_search: True if query contains search keywords
                - raw_query: Original query
                - shell_cmd: Extracted shell command (if prefixed with !)
                - file_path: Extracted file path (if found)
                
        Raises:
            ValidationError: If query is not a string
            
        Example:
            >>> shell = AstroShell()
            >>> intent = shell.analyze_intent("!ls -la")
            >>> intent['wants_shell']
            True
        """
        if not isinstance(query, str):
            raise ValidationError(f"Query must be a string, got {type(query).__name__}")
        
        q = query.strip().lower()

        flags: Dict[str, Any] = {
            "wants_shell": q.startswith("!"),   # explicit shell command
            "wants_file_read": bool(re.search(r"\b(read|show|cat|view)\b", q)),
            "wants_search": bool(re.search(r"\b(find|search|where|locate)\b", q)),
            "raw_query": query,
        }
        
        # Extract inline command if prefixed with !
        m = re.match(r"^!(.+)", query.strip())
        if m:
            flags["shell_cmd"] = m.group(1).strip()

        # Look for file path hints: path in quotes or after 'read'
        m2 = re.search(r"(?:read|show|cat)\s+['\"]?([^'\"]+)['\"]?", query, re.IGNORECASE)
        if m2:
            flags["file_path"] = m2.group(1).strip()

        return flags

    def reason(
        self,
        query: str,
        intent: Dict[str, Any],
        thoughts: List[Dict[str, Any]],
        actions_taken: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simple reasoning rules based on analyzed intent and past observations.
        
        Args:
            query: The original user query
            intent: Intent flags from analyze_intent()
            thoughts: List of previous thought dictionaries
            actions_taken: List of previous action results
            
        Returns:
            Thought dictionary with:
                - thought: Reasoning text
                - action: Optional action dict (format: {"tool": "...", "args": {...}})
                - done: Optional boolean indicating completion
                - error: Optional error message
                
        Example:
            >>> shell = AstroShell()
            >>> intent = {"wants_shell": True, "shell_cmd": "ls"}
            >>> thought = shell.reason("!ls", intent, [], [])
            >>> thought['action']['tool']
            'shell'
        """
        try:
            # If explicit shell command requested
            if intent.get("wants_shell") and intent.get("shell_cmd"):
                return {
                    "thought": "User requested shell execution",
                    "action": {"tool": "shell", "cmd": intent["shell_cmd"]}
                }

            # If user asked to read a file
            if (intent.get("wants_file_read") and
                    intent.get("file_path") and
                    not any(a["action"].get("tool") == "read_file"
                            for a in actions_taken if isinstance(a.get("action"), dict))):
                return {
                    "thought": f"Read file {intent.get('file_path')}",
                    "action": {"tool": "read_file", "path": intent["file_path"]}
                }

            # If user asked to search for something in the repo/workspace
            if intent.get("wants_search"):
                # Try to extract a short search term
                m = re.search(r"(?:find|search for|where is)\s+(.+)", query, re.IGNORECASE)
                term = (m.group(1).strip() if m else query)
                return {
                    "thought": f"Search for '{term}'",
                    "action": {"tool": "search", "pattern": term, "path": "."}
                }

            # Default: no external action, produce an answer
            return {"thought": "Formulate an answer from context", "done": True}
        except Exception as e:
            logger.exception("Error in reason()")
            return {"thought": "Error during reasoning", "done": True, "error": str(e)}

    # -----------------------
    # Tools (act)
    # -----------------------
    def act(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single action. Return a structured result dict.
        
        Supported tools: shell, read_file, search
        
        Args:
            action: Action dictionary with 'tool' key and tool-specific args
            
        Returns:
            Result dictionary with:
                - success: Boolean indicating success
                - output: Output string (on success)
                - error: Error message (on failure)
                
        Raises:
            ValidationError: If action is not a valid dict
            ToolExecutionError: If tool execution fails unexpectedly
            
        Example:
            >>> shell = AstroShell()
            >>> result = shell.act({"tool": "shell", "cmd": "echo hello"})
            >>> result['success']
            True
        """
        if not isinstance(action, dict):
            raise ValidationError("Action must be a dictionary")
        
        tool = action.get("tool")
        if not tool:
            return {"success": False, "error": "Action missing 'tool' key"}
        
        try:
            if tool == "shell":
                cmd = action.get("cmd", "")
                if not isinstance(cmd, str):
                    return {"success": False, "error": "cmd must be a string"}
                return {"success": True, "output": self._tool_shell(cmd)}
            if tool == "read_file":
                path = action.get("path", "")
                if not isinstance(path, str):
                    return {"success": False, "error": "path must be a string"}
                return {"success": True, "output": self._tool_read_file(path)}
            if tool == "search":
                pattern = action.get("pattern", "")
                path = action.get("path", ".")
                if not isinstance(pattern, str):
                    return {"success": False, "error": "pattern must be a string"}
                if not isinstance(path, str):
                    return {"success": False, "error": "path must be a string"}
                return {"success": True, "output": self._tool_search(pattern, path)}
            return {"success": False, "error": f"Unsupported tool: {tool}"}
        except ToolExecutionError as e:
            logger.exception("Tool execution error")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception("Error executing action")
            return {"success": False, "error": f"Unexpected error: {e}"}

    def _tool_shell(self, cmd: str, timeout: int = 20) -> str:
        """
        Run a shell command in a safe manner and return output (stdout+stderr).
        
        Args:
            cmd: The shell command to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            Command output string (stdout + stderr), truncated to MAX_OUTPUT_LENGTH
            
        Raises:
            ValidationError: If cmd is empty or not a string
            ToolExecutionError: If command execution fails
            
        Example:
            >>> shell = AstroShell()
            >>> output = shell._tool_shell("echo hello")
            >>> "hello" in output
            True
        """
        if not isinstance(cmd, str):
            raise ValidationError(f"Command must be a string, got {type(cmd).__name__}")
        
        if not cmd.strip():
            return "(no command)"
        
        # Security: Reject dangerous commands
        dangerous_patterns = [
            r";\s*rm\s+-rf\s+/",
            r">\s*/dev/null.*2>&1.*rm",
            r":\(\)\s*\{\s*:\|:&\s*\};:",  # fork bomb
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, cmd):
                return "(rejected: potentially dangerous command)"
        
        try:
            completed = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout, 
                cwd=str(self.cwd)
            )
            out = (completed.stdout or "") + (completed.stderr or "")
            out = out.strip()
            if not out:
                return "(no output)"
            return out[:MAX_OUTPUT_LENGTH]  # truncate to reasonable size
        except subprocess.TimeoutExpired:
            return f"(timed out after {timeout}s)"
        except subprocess.SubprocessError as e:
            logger.debug("Shell subprocess error: %s", e)
            return f"(shell error: {e})"
        except Exception as e:
            logger.debug("Shell execution error: %s", e)
            return f"(error executing shell: {e})"

    def _tool_read_file(self, path: str) -> str:
        """
        Read a file content safely and return a truncated result.
        
        Args:
            path: Path to the file (relative or absolute)
            
        Returns:
            File content string, truncated to MAX_OUTPUT_LENGTH if too long
            
        Raises:
            ValidationError: If path is not a string
            ToolExecutionError: If file cannot be read
            
        Example:
            >>> shell = AstroShell()
            >>> content = shell._tool_read_file("README.md")
            >>> isinstance(content, str)
            True
        """
        if not isinstance(path, str):
            raise ValidationError(f"Path must be a string, got {type(path).__name__}")
        
        try:
            p = Path(path).expanduser()
            if not p.is_absolute():
                p = self.cwd / p
            
            # Security: Check for path traversal
            try:
                p.resolve().relative_to(self.cwd.resolve())
            except ValueError:
                raise ToolExecutionError(f"Attempted to read file outside working directory: {p}")
            if not p.exists():
                return f"(file not found: {p})"
            
            if not p.is_file():
                return f"(not a file: {p})"
            
            content = p.read_text(errors="replace")
            if len(content) > MAX_OUTPUT_LENGTH:
                return content[:MAX_OUTPUT_LENGTH] + f"\n... (truncated, {len(content)} chars total)"
            return content
        except (OSError, IOError) as e:
            logger.debug("Read file error: %s", e)
            return f"(error reading file: {e})"
        except Exception as e:
            logger.debug("Read file unexpected error: %s", e)
            return f"(error reading file: {e})"

    def _tool_search(self, pattern: str, path: str = ".") -> str:
        """
        Simple file search using grep (shell) for portability.
        
        Returns the first chunk of results. Falls back to Python implementation
        if grep fails.
        
        Args:
            pattern: Search pattern string
            path: Directory path to search in (default: current directory)
            
        Returns:
            Search results string
            
        Raises:
            ValidationError: If pattern or path is not a string
            
        Example:
            >>> shell = AstroShell()
            >>> results = shell._tool_search("def main", ".")
            >>> isinstance(results, str)
            True
        """
        if not isinstance(pattern, str):
            raise ValidationError(f"Pattern must be a string, got {type(pattern).__name__}")
        if not isinstance(path, str):
            raise ValidationError(f"Path must be a string, got {type(path).__name__}")
        
        if not pattern.strip():
            return "(empty search pattern)"
        
        try:
            # Sanitize pattern to avoid shell injection: use shlex.quote for pattern
            safe_pattern = shlex.quote(pattern)
            safe_path = shlex.quote(path)
            cmd = f"grep -rn {safe_pattern} {safe_path} 2>/dev/null | head -n 50"
            completed = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=str(self.cwd), 
                timeout=20
            )
            out = (completed.stdout or "").strip()
            return out if out else "(no matches)"
        except subprocess.TimeoutExpired:
            return "(search timed out)"
        except subprocess.SubprocessError as e:
            logger.debug("Search subprocess error, falling back to Python: %s", e)
        except Exception as e:
            logger.debug("Search error; falling back to python search: %s", e)
        
        # Fallback: walk files and do simple substring search
        return self._fallback_search(pattern, path)

    def _fallback_search(self, pattern: str, path: str) -> str:
        """
        Fallback Python-based file search.
        
        Args:
            pattern: Search pattern string
            path: Directory path to search in
            
        Returns:
            Search results string
        """
        results: List[str] = []
        binary_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf",
            ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".dylib"
        }
        
        try:
            p = Path(path)
            if not p.is_absolute():
                p = self.cwd / p
            
            for f in p.rglob("*"):
                if f.is_file() and f.suffix.lower() not in binary_extensions:
                    try:
                        txt = f.read_text(errors="ignore")
                        if pattern.lower() in txt.lower():
                            results.append(f"{f}: (match)")
                            if len(results) >= 30:
                                break
                    except (OSError, IOError):
                        continue
                    except Exception:
                        continue
            return "\n".join(results) if results else "(no matches)"
        except (OSError, IOError) as e:
            return f"(error performing search: {e})"
        except Exception as e:
            return f"(error performing search: {e})"

    def is_sufficient(self, query: str, actions_taken: List[Dict[str, Any]]) -> bool:
        """
        Decide whether collected observations are sufficient to synthesize a final answer.
        
        Very conservative: return True if any action returned non-empty useful output.
        
        Args:
            query: Original user query
            actions_taken: List of action results
            
        Returns:
            True if sufficient information has been gathered
            
        Example:
            >>> shell = AstroShell()
            >>> actions = [{"action": {"tool": "shell"}, "result": {"success": True, "output": "test"}}]
            >>> shell.is_sufficient("test", actions)
            True
        """
        try:
            if not actions_taken:
                return False
            
            # If the most recent action succeeded and had non-empty output, it's sufficient
            last = actions_taken[-1].get("result", {})
            if last.get("success") and last.get("output"):
                return True
            
            # If any previous action had a success+output
            for a in reversed(actions_taken):
                r = a.get("result", {})
                if r.get("success") and r.get("output"):
                    return True
            return False
        except (TypeError, AttributeError) as e:
            logger.debug("is_sufficiency type error: %s", e)
            return False
        except Exception as e:
            logger.debug("is_sufficient error: %s", e)
            return False

    def synthesize(
        self,
        query: str,
        thoughts: List[Dict[str, Any]],
        actions_taken: List[Dict[str, Any]]
    ) -> str:
        """
        Turn thoughts and actions into a final response string.
        
        Keep the output concise and user-friendly.
        
        Args:
            query: Original user query
            thoughts: List of thought dictionaries
            actions_taken: List of action results
            
        Returns:
            Formatted response string
            
        Example:
            >>> shell = AstroShell()
            >>> result = shell.synthesize("test", [], [])
            >>> isinstance(result, str)
            True
        """
        try:
            # If there are actions with outputs, present them clearly.
            if actions_taken:
                parts: List[str] = []
                for i, act_entry in enumerate(actions_taken, start=1):
                    action = act_entry.get("action", {})
                    result = act_entry.get("result", {})
                    tool = action.get("tool", "<unknown>")
                    parts.append(f"--- Action {i}: {tool} ---")
                    if result.get("success"):
                        parts.append(result.get("output", "(no output)"))
                    else:
                        parts.append(f"(error) {result.get('error', 'unknown')}")
                return "\n".join(parts)

            # Otherwise present a helpful message based on thoughts
            if thoughts:
                last = thoughts[-1]
                if last.get("done"):
                    return "OK. " + (last.get("answer") or "I'm done.")
                return last.get("thought", "I don't have enough information.")
            return "I don't have enough information to proceed."
        except (TypeError, AttributeError) as e:
            logger.exception("synthesize type error: %s", e)
            return "An error occurred while creating the response."
        except Exception as e:
            logger.exception("synthesize failed: %s", e)
            return "An error occurred while creating the response."


if __name__ == "__main__":
    shell = AstroShell()
    import argparse

    p = argparse.ArgumentParser(description="Run ASTRO Shell simple CLI")
    p.add_argument("message", nargs="*", help="The message to send")
    args = p.parse_args()
    if args.message:
        msg = " ".join(args.message)
        print(shell.chat(msg))
    else:
        # Interactive loop
        try:
            while True:
                inp = input("> ")
                if not inp.strip():
                    continue
                if inp.strip() in {"exit", "quit"}:
                    break
                try:
                    print(shell.chat(inp))
                except ValidationError as e:
                    print(f"Error: {e}")
                except Exception as e:
                    logger.exception("Error processing input")
                    print(f"Error: {e}")
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
        finally:
            shell.save_history()
