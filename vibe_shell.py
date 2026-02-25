#!/usr/bin/env python3
"""
ASTRO Vibe Shell - Async LLM-powered ReAct orchestrator.

Bridges natural language and your local Linux environment using an async ReAct
(Reasoning + Acting) loop powered by LLM providers (Anthropic/OpenAI).

Features:
- Async/await support for all I/O operations
- Natural language command processing
- Multiple LLM provider support with fallback chain (Anthropic -> OpenAI -> Local)
- Async tool execution (shell, file read/write, search)
- Automatic retry logic with exponential backoff
- Comprehensive error handling
- Session persistence

Environment Variables:
    ANTHROPIC_API_KEY: API key for Anthropic Claude
    OPENAI_API_KEY: API key for OpenAI
    ASTRO_API: Base URL for ASTRO API (default: http://localhost:5000/api/v1)

Example usage:
    import asyncio
    
    async def main():
        shell = VibeShell()
        await shell.initialize()
        await shell.run()  # Start interactive mode
        
    asyncio.run(main())
    
    # Or single command
    response = await shell.react("show me all Python files")
    print(response)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import readline
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

import aiohttp
import aiofiles

# Optional LLM imports with graceful degradation
try:
    from openai import AsyncOpenAI, OpenAIError
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAIError = Exception

try:
    from anthropic import AsyncAnthropic, AnthropicError
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    AnthropicError = Exception

# Config
API_BASE = os.getenv("ASTRO_API", "http://localhost:5000/api/v1")
SESSION_FILE = Path.home() / ".vibe_session"
HISTORY_FILE = Path.home() / ".vibe_history"

# Constants
DEFAULT_TIMEOUT = 30
MAX_LLM_RETRIES = 3
LLM_RETRY_DELAY = 1.0  # seconds
MAX_OUTPUT_LENGTH = 4000
MAX_STEPS = 6
CHUNK_SIZE = 8192


# Setup logger with structured JSON format for auditability
def _setup_logger() -> logging.Logger:
    """Setup and configure the vibe_shell logger with structured JSON output."""
    logger = logging.getLogger("vibe_shell")
    if not logger.handlers:
        handler = logging.StreamHandler()

        # Use JSON formatter for structured logging
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "user": getattr(record, "user", os.getenv("USER", "unknown")),
                    "action": getattr(record, "action", None),
                    "outcome": getattr(record, "outcome", None),
                }
                # Include any additional context from kwargs
                for key, value in getattr(record, "context", {}).items():
                    if key not in log_entry:
                        log_entry[key] = value
                # Include exception info if present
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                return json.dumps(log_entry)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def log_audit(logger, level, message, action=None, outcome=None, **kwargs):
    """Log an audit event with context."""
    extra = {"user": os.getenv("USER", "unknown"), "action": action,
             "outcome": outcome, "context": kwargs}
    logger.log(level, message, extra=extra)


logger = _setup_logger()


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


class VibeShellError(Exception):
    """Base exception for VibeShell errors."""
    pass


class AuthenticationError(VibeShellError):
    """Raised when authentication fails."""
    pass


class LLMError(VibeShellError):
    """Raised when LLM communication fails."""
    pass


class ToolExecutionError(VibeShellError):
    """Raised when tool execution fails."""
    pass


class ValidationError(VibeShellError):
    """Raised when input validation fails."""
    pass


@dataclass
class Action:
    """Represents a tool action to be executed."""
    tool: str
    args: Dict[str, Any]
    
    def __post_init__(self) -> None:
        """Validate action after creation."""
        if not isinstance(self.tool, str) or not self.tool:
            raise ValidationError("Action tool must be a non-empty string")
        if not isinstance(self.args, dict):
            raise ValidationError("Action args must be a dictionary")


@dataclass
class Step:
    """Represents a single step in the ReAct loop."""
    thought: str
    action: Optional[Action] = None
    observation: Optional[str] = None
    answer: Optional[str] = None


@dataclass
class LLMProvider:
    """Represents an LLM provider configuration."""
    name: str
    client: Any
    priority: int  # Lower = higher priority
    is_available: bool = True


class VibeShell:
    """
    Async LLM-powered ReAct orchestrator for natural language system interaction.
    
    This class provides an interactive shell that processes natural language
    queries using an async ReAct (Reasoning + Acting) loop powered by LLM providers.
    
    Attributes:
        cwd: Current working directory
        token: Authentication token for API access
        history: Conversation history
        llm_providers: List of configured LLM providers (ordered by priority)
        session: aiohttp ClientSession for HTTP requests
        
    Example:
        >>> import asyncio
        >>> async def main():
        ...     shell = VibeShell()
        ...     await shell.initialize()
        ...     result = await shell.react("list all files")
        ...     print(result)
        >>> asyncio.run(main())
    """

    def __init__(self) -> None:
        """Initialize the VibeShell instance."""
        self.cwd: str = os.getcwd()
        self.token: Optional[str] = None
        self.history: List[Dict[str, Any]] = []
        self.llm_providers: List[LLMProvider] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self._initialized: bool = False
        
    async def initialize(self) -> None:
        """
        Initialize async resources and load session.
        
        Must be called before using other async methods.
        
        Example:
            >>> shell = VibeShell()
            >>> await shell.initialize()
        """
        if self._initialized:
            return
            
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Initialize LLM clients
        await self._init_llm_providers()
        
        # Load session and authenticate
        await self._load_session_async()
        self.setup_readline()
        
        self._initialized = True
        logger.debug("VibeShell initialized successfully")
        
    async def cleanup(self) -> None:
        """
        Cleanup async resources.
        
        Should be called when done using the shell.
        
        Example:
            >>> await shell.cleanup()
        """
        self.save_history()
        if self.session:
            await self.session.close()
            self.session = None
        self._initialized = False
        
    async def _init_llm_providers(self) -> None:
        """
        Initialize LLM providers based on available API keys.
        
        Priority: Anthropic > OpenAI
        """
        providers: List[LLMProvider] = []
        
        # Anthropic (highest priority)
        if HAS_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY"):
            try:
                client = AsyncAnthropic()
                providers.append(LLMProvider(
                    name="anthropic",
                    client=client,
                    priority=1
                ))
                logger.info("Initialized Anthropic client")
            except Exception as e:
                logger.warning("Failed to initialize Anthropic: %s", e)
        
        # OpenAI (second priority)
        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            try:
                client = AsyncOpenAI()
                providers.append(LLMProvider(
                    name="openai",
                    client=client,
                    priority=2
                ))
                logger.info("Initialized OpenAI client")
            except Exception as e:
                logger.warning("Failed to initialize OpenAI: %s", e)
        
        # Sort by priority
        self.llm_providers = sorted(providers, key=lambda p: p.priority)
        
        if not self.llm_providers:
            logger.warning("No LLM providers available. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
    
    def setup_readline(self) -> None:
        """
        Setup readline with history file support.
        
        Loads previous command history if available.
        """
        try:
            if HISTORY_FILE.exists():
                readline.read_history_file(str(HISTORY_FILE))
        except (OSError, IOError) as e:
            logger.debug("Failed to read history file: %s", e)
        except Exception as e:
            logger.debug("Unexpected error reading history: %s", e)
        
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
            logger.debug("Unexpected error saving history: %s", e)
    
    async def _load_session_async(self) -> None:
        """
        Load existing session or attempt to authenticate asynchronously.
        """
        if SESSION_FILE.exists():
            try:
                async with aiofiles.open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                    self.token = data.get("token")
                    if self.token:
                        logger.debug("Loaded existing session")
            except json.JSONDecodeError as e:
                logger.debug("Failed to parse session file: %s", e)
            except (OSError, IOError) as e:
                logger.debug("Failed to read session file: %s", e)
            except Exception as e:
                logger.debug("Unexpected error loading session: %s", e)
        
        if not self.token:
            await self._authenticate_async()
    
    async def _authenticate_async(self, timeout: int = 5, max_retries: int = 2) -> None:
        """
        Authenticate with the ASTRO API to obtain a dev token asynchronously.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        if not self.session:
            raise VibeShellError("Session not initialized")
            
        for attempt in range(max_retries):
            try:
                url = f"{API_BASE}/auth/dev-token"
                payload = {
                    "userId": os.getenv("USER", "user"),
                    "role": "admin"
                }
                
                async with self.session.post(url, json=payload, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.token = data.get("token")
                        if self.token:
                            await self._save_session_async()
                            logger.info("Authenticated with ASTRO API")
                            return
                    else:
                        logger.debug("Auth returned non-ok status: %d", resp.status)
                        
            except asyncio.TimeoutError:
                logger.debug("Authentication attempt %d timed out", attempt + 1)
            except aiohttp.ClientError as e:
                logger.debug("Auth connection error (attempt %d): %s", attempt + 1, e)
            except Exception as e:
                logger.debug("Auth unexpected error (attempt %d): %s", attempt + 1, e)
        
        logger.debug("Authentication failed after %d attempts", max_retries)
    
    async def _save_session_async(self) -> None:
        """Save session to file asynchronously."""
        try:
            async with aiofiles.open(SESSION_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps({"token": self.token}, indent=2))
        except (OSError, IOError) as e:
            logger.debug("Failed to save session: %s", e)
        except Exception as e:
            logger.debug("Unexpected error saving session: %s", e)

    # ==================== ASYNC TOOLS ====================
    
    async def tool_shell(self, cmd: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Execute a shell command asynchronously.
        
        Args:
            cmd: Shell command to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            Command output (stdout + stderr), truncated to MAX_OUTPUT_LENGTH
            
        Raises:
            ValidationError: If cmd is not a string
            ToolExecutionError: If command execution fails
            
        Example:
            >>> shell = VibeShell()
            >>> await shell.initialize()
            >>> output = await shell.tool_shell("echo hello")
            >>> "hello" in output.lower()
            True
        """
        if not isinstance(cmd, str):
            raise ValidationError(f"Command must be a string, got {type(cmd).__name__}")
        
        cmd = cmd.strip()
        if not cmd:
            return "(no command)"
        
        # Security: Block dangerous commands (comprehensive blacklist)
        dangerous_patterns = [
            (r";\s*rm\s+-rf\s+/", "recursive root deletion"),
            (r">\s*/dev/null.*rm.*-rf", "masked deletion"),
            (r":\(\)\s*\{\s*:\|:&\s*\};:", "fork bomb"),
            (r"rm\s+-rf\s+/\s*\*", "wildcard root deletion"),
            (r"dd\s+if=\S+\s+of=/dev/[sh]d", "disk destruction"),
            (r"mkfs\.\w+\s+/dev/[sh]d", "filesystem destruction"),
            (r">\s*/dev/[sh]d[a-z]?\b", "direct disk write"),
            (r"curl\s+.*\|\s*sh", "pipe to shell"),
            (r"wget\s+.*\|\s*sh", "pipe to shell"),
            (r"bash\s+-c\s+.*\$\(", "command substitution"),
            (r"eval\s*\$", "eval with variable"),
            (r"sudo\s+rm\s+-rf", "sudo recursive deletion"),
        ]
        
        for pattern, description in dangerous_patterns:
            if re.search(pattern, cmd, re.IGNORECASE):
                log_audit(logger, logging.WARNING,
                          f"Blocked dangerous command ({description}): {cmd[:50]}",
                          action="shell", outcome="blocked")
                return f"(blocked: potentially dangerous command - {description})"

        # Audit log shell execution attempt (log cmd hash only for security)
        cmd_hash = hash(cmd) & 0xFFFFFFFF
        log_audit(logger, logging.INFO, f"Shell execution attempted (cmd_hash: {cmd_hash})",
                  action="shell", outcome="attempted", cmd_hash=cmd_hash)
        
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                output = (stdout.decode('utf-8', errors='replace') +
                          stderr.decode('utf-8', errors='replace')).strip()
                result = output[:MAX_OUTPUT_LENGTH] if output else "(no output)"
                log_audit(logger, logging.INFO, f"Shell execution completed (cmd_hash: {cmd_hash})",
                          action="shell", outcome="success", cmd_hash=cmd_hash)
                return result
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                log_audit(logger, logging.WARNING, f"Shell execution timed out (cmd_hash: {cmd_hash})",
                          action="shell", outcome="timeout", cmd_hash=cmd_hash, timeout=timeout)
                return f"(timed out after {timeout}s)"

        except Exception as e:
            logger.debug("Shell execution error: %s", e)
            log_audit(logger, logging.ERROR, f"Shell execution failed (cmd_hash: {cmd_hash})",
                      action="shell", outcome="error", cmd_hash=cmd_hash, error_type=type(e).__name__)
            return "(error executing command)"
    
    async def tool_read_file(self, path: str) -> str:
        """
        Read file contents asynchronously.
        
        Args:
            path: Path to the file (relative or absolute)
            
        Returns:
            File content string, truncated to MAX_OUTPUT_LENGTH if too long
            
        Raises:
            ValidationError: If path is not a string
            
        Example:
            >>> shell = VibeShell()
            >>> await shell.initialize()
            >>> content = await shell.tool_read_file("README.md")
            >>> isinstance(content, str)
            True
        """
        if not isinstance(path, str):
            raise ValidationError(f"Path must be a string, got {type(path).__name__}")
        
        try:
            p = Path(path).expanduser()
            if not p.is_absolute():
                p = Path(self.cwd) / p
            
            # Security: Resolve and validate path is within working directory
            try:
                p.resolve().relative_to(Path(self.cwd).resolve())
            except ValueError:
                log_audit(logger, logging.WARNING, 
                         f"Attempted path traversal blocked: {path}",
                         action="read_file", outcome="blocked")
                return "(access denied: path outside working directory)"
            
            if not p.exists():
                return f"(file not found: {p})"
            
            if not p.is_file():
                return f"(not a file: {p})"
            
            # Read file asynchronously
            async with aiofiles.open(p, 'r', encoding='utf-8', errors='replace') as f:
                content = await f.read()
                log_audit(logger, logging.INFO, f"File read: {p}",
                         action="read_file", outcome="success")
                if len(content) > MAX_OUTPUT_LENGTH:
                    return content[:MAX_OUTPUT_LENGTH] + f"\n... (truncated, {len(content)} total chars)"
                return content
                
        except (OSError, IOError) as e:
            logger.debug("Read file error: %s", e)
            return f"(error reading {path}: {e})"
        except Exception as e:
            logger.debug("Read file unexpected error: %s", e)
            return f"(error reading {path}: {e})"
    
    async def tool_write_file(self, path: str, content: str) -> str:
        """
        Write content to a file asynchronously.
        
        Args:
            path: Path to the file (relative or absolute)
            content: Content to write
            
        Returns:
            Success message with character count
            
        Raises:
            ValidationError: If path or content is not a string
            
        Example:
            >>> shell = VibeShell()
            >>> await shell.initialize()
            >>> result = await shell.tool_write_file("/tmp/test.txt", "hello")
            >>> "Written" in result
            True
        """
        if not isinstance(path, str):
            raise ValidationError(f"Path must be a string, got {type(path).__name__}")
        if not isinstance(content, str):
            raise ValidationError(f"Content must be a string, got {type(content).__name__}")
        
        try:
            p = Path(path).expanduser()
            if not p.is_absolute():
                p = Path(self.cwd) / p
            
            # Security: Resolve and validate path is within working directory
            try:
                p.resolve().relative_to(Path(self.cwd).resolve())
            except ValueError:
                log_audit(logger, logging.WARNING,
                         f"Attempted path traversal blocked: {path}",
                         action="write_file", outcome="blocked")
                return "(access denied: path outside working directory)"
            
            # Create parent directories if needed
            p.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(p, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            log_audit(logger, logging.INFO, f"File written: {p}",
                     action="write_file", outcome="success")
                
            return f"✓ Written {len(content)} chars to {p}"
            
        except (OSError, IOError) as e:
            logger.debug("Write file error: %s", e)
            return f"(error writing {path}: {e})"
        except Exception as e:
            logger.debug("Write file unexpected error: %s", e)
            return f"(error writing {path}: {e})"
    
    async def tool_search(self, pattern: str, path: str = ".") -> str:
        """
        Search for pattern in files asynchronously.
        
        Args:
            pattern: Search pattern string
            path: Directory path to search in (default: current directory)
            
        Returns:
            Search results string
            
        Raises:
            ValidationError: If pattern or path is not a string
            
        Example:
            >>> shell = VibeShell()
            >>> await shell.initialize()
            >>> results = await shell.tool_search("def main", ".")
            >>> isinstance(results, str)
            True
        """
        if not isinstance(pattern, str):
            raise ValidationError(f"Pattern must be a string, got {type(pattern).__name__}")
        if not isinstance(path, str):
            raise ValidationError(f"Path must be a string, got {type(path).__name__}")
        
        if not pattern.strip():
            return "(empty search pattern)"
        
        # Sanitize inputs - use -- to prevent patterns starting with - from being interpreted as options
        safe_pattern = shlex.quote(pattern)
        safe_path = shlex.quote(path)
        cmd = f"grep -rn -- {safe_pattern} {safe_path} 2>/dev/null | head -30"
        
        return await self.tool_shell(cmd, timeout=20)
    
    async def execute_action(self, action: Action) -> str:
        """
        Execute a tool action asynchronously.
        
        Args:
            action: Action object containing tool name and arguments
            
        Returns:
            Tool execution result string
            
        Raises:
            ValidationError: If action is invalid
            
        Example:
            >>> shell = VibeShell()
            >>> await shell.initialize()
            >>> action = Action("shell", {"cmd": "echo hello"})
            >>> result = await shell.execute_action(action)
            >>> "hello" in result.lower()
            True
        """
        if not isinstance(action, Action):
            raise ValidationError(f"Expected Action, got {type(action).__name__}")
        
        tool_map: Dict[str, Callable[[Dict[str, Any]], Coroutine[Any, Any, str]]] = {
            "shell": lambda a: self.tool_shell(a.get("cmd", "")),
            "read_file": lambda a: self.tool_read_file(a.get("path", "")),
            "write_file": lambda a: self.tool_write_file(
                a.get("path", ""),
                a.get("content", "")
            ),
            "search": lambda a: self.tool_search(
                a.get("pattern", ""),
                a.get("path", ".")
            ),
        }
        
        handler = tool_map.get(action.tool)
        if handler:
            try:
                return await handler(action.args)
            except Exception as e:
                logger.exception("Action execution error")
                return f"(error executing {action.tool}: {e})"
        
        return f"(unknown tool: {action.tool})"

    # ==================== LLM ORCHESTRATION ====================
    
    async def call_llm_with_fallback(
        self,
        messages: List[Dict[str, str]],
        max_retries: int = MAX_LLM_RETRIES,
        retry_delay: float = LLM_RETRY_DELAY
    ) -> str:
        """
        Call LLM API with provider fallback and retry logic.
        
        Tries providers in priority order with exponential backoff.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_retries: Maximum retry attempts per provider
            retry_delay: Initial delay between retries
            
        Returns:
            LLM response text, or error message if all providers fail
            
        Example:
            >>> shell = VibeShell()
            >>> await shell.initialize()
            >>> messages = [{"role": "user", "content": "Hello"}]
            >>> response = await shell.call_llm_with_fallback(messages)
        """
        if not self.llm_providers:
            return "ANSWER: No LLM providers available. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
        
        last_error = ""
        
        for provider in self.llm_providers:
            if not provider.is_available:
                continue
                
            for attempt in range(max_retries):
                try:
                    if provider.name == "anthropic":
                        return await self._call_anthropic(provider.client, messages)
                    elif provider.name == "openai":
                        return await self._call_openai(provider.client, messages)
                        
                except (AnthropicError, OpenAIError) as e:
                    last_error = str(e)
                    logger.warning("%s API error (attempt %d): %s", provider.name, attempt + 1, e)
                    if attempt < max_retries - 1:
                        sleep_time = retry_delay * (2 ** attempt)
                        logger.debug("Retrying in %.1f seconds...", sleep_time)
                        await asyncio.sleep(sleep_time)
                    else:
                        provider.is_available = False
                        
                except Exception as e:
                    last_error = str(e)
                    logger.exception("Unexpected error calling %s", provider.name)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                    else:
                        provider.is_available = False
        
        return f"ANSWER: All LLM providers failed. Last error: {last_error}"
    
    async def _call_anthropic(
        self,
        client: AsyncAnthropic,
        messages: List[Dict[str, str]]
    ) -> str:
        """
        Call Anthropic Claude API asynchronously.
        
        Args:
            client: AsyncAnthropic client instance
            messages: List of message dictionaries
            
        Returns:
            Response text from Claude
        """
        # Extract system message
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]
        
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system,
            messages=user_msgs
        )
        return response.content[0].text
    
    async def _call_openai(
        self,
        client: AsyncOpenAI,
        messages: List[Dict[str, str]]
    ) -> str:
        """
        Call OpenAI API asynchronously.
        
        Args:
            client: AsyncOpenAI client instance
            messages: List of message dictionaries
            
        Returns:
            Response text from GPT
        """
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2000
        )
        return response.choices[0].message.content

    # ==================== ReAct LOOP ====================
    
    def parse_llm_response(self, text: str) -> Step:
        """
        Parse LLM response into a Step object.
        
        Args:
            text: Raw LLM response text
            
        Returns:
            Step object containing parsed thought, action, and/or answer
        """
        step = Step(thought="")
        
        if not isinstance(text, str):
            logger.warning("LLM response is not a string: %s", type(text))
            return step
        
        # Extract THOUGHT
        thought_match = re.search(r'THOUGHT:\s*(.+?)(?=ACTION:|ANSWER:|$)', text, re.DOTALL)
        if thought_match:
            step.thought = thought_match.group(1).strip()
        
        # Extract ACTION
        action_match = re.search(r'ACTION:\s*(\w+)\((.+?)\)', text, re.DOTALL)
        if action_match:
            tool = action_match.group(1)
            args_str = action_match.group(2).strip()
            args: Dict[str, Any] = self._parse_action_args(tool, args_str)
            
            try:
                step.action = Action(tool=tool, args=args)
            except ValidationError as e:
                logger.warning("Invalid action from LLM: %s", e)
        
        # Extract ANSWER
        answer_match = re.search(r'ANSWER:\s*(.+?)$', text, re.DOTALL)
        if answer_match:
            step.answer = answer_match.group(1).strip()
        
        return step
    
    def _parse_action_args(self, tool: str, args_str: str) -> Dict[str, Any]:
        """Parse action arguments based on tool type."""
        args: Dict[str, Any] = {}
        
        if tool == "shell":
            args["cmd"] = args_str.strip('"\'')
        elif tool == "read_file":
            args["path"] = args_str.strip('"\'')
        elif tool == "write_file":
            # Try double quotes first
            parts = re.match(r'"([^"]+)"\s*,\s*"(.+)"', args_str, re.DOTALL)
            if parts:
                args["path"] = parts.group(1)
                args["content"] = parts.group(2)
            else:
                # Try single quotes
                parts = re.match(r"'([^']+)'\s*,\s*'(.+)'", args_str, re.DOTALL)
                if parts:
                    args["path"] = parts.group(1)
                    args["content"] = parts.group(2)
        elif tool == "search":
            parts = args_str.split(",", 1)
            args["pattern"] = parts[0].strip().strip('"\'')
            if len(parts) > 1:
                args["path"] = parts[1].strip().strip('"\'')
        
        return args
    
    async def react(self, user_input: str) -> str:
        """
        Run async ReAct loop for user query.
        
        The ReAct loop iteratively reasons about the query, takes actions,
        observes results, and synthesizes a final answer.
        
        Args:
            user_input: Natural language query from the user
            
        Returns:
            Final answer string
            
        Raises:
            ValidationError: If user_input is not a string
            
        Example:
            >>> shell = VibeShell()
            >>> await shell.initialize()
            >>> result = await shell.react("What files are here?")
        """
        if not isinstance(user_input, str):
            raise ValidationError(f"Input must be a string, got {type(user_input).__name__}")
        
        user_input = user_input.strip()
        if not user_input:
            return "Please enter a command or question."
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Current directory: {self.cwd}\n\nUser: {user_input}"}
        ]
        
        steps: List[Step] = []
        
        for i in range(MAX_STEPS):
            # Get LLM response
            response = await self.call_llm_with_fallback(messages)
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
                args_preview = json.dumps(step.action.args)[:60]
                print(f"⚡ {step.action.tool}({args_preview}...)")
                observation = await self.execute_action(step.action)
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
    
    async def handle_builtin(self, cmd: str) -> Optional[str]:
        """
        Handle built-in shell commands.
        
        Args:
            cmd: Command string to handle
            
        Returns:
            Response string if handled, None if not a built-in command
        """
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
            except (OSError, IOError) as e:
                return f"Error changing directory: {e}"
            except Exception as e:
                return f"Error: {e}"
        
        if builtin == "pwd":
            return self.cwd
        
        if builtin in ["exit", "quit", "q"]:
            self.save_history()
            print("\n👋 Bye!")
            sys.exit(0)
        
        if builtin == "clear":
            try:
                os.system("clear")
            except Exception:
                pass
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
        """
        Check if input is a direct shell command.
        
        Args:
            cmd: Command string to check
            
        Returns:
            True if the command should be executed directly as a shell command
        """
        direct_cmds = [
            "ls", "cat", "grep", "find", "git", "npm", "python", "python3", "node",
            "make", "cargo", "go", "docker", "kubectl", "curl", "wget",
            "head", "tail", "less", "vim", "nano", "code", "tree", "ps",
            "top", "htop", "df", "du", "chmod", "chown", "mkdir", "rm",
            "cp", "mv", "touch", "echo", "which", "man", "ssh", "scp",
            "tar", "zip", "unzip", "ping", "netstat", "lsof", "kill",
            "pgrep", "pkill", "history", "alias", "export", "source"
        ]
        
        cmd = cmd.strip()
        if not cmd:
            return False
        
        first = cmd.split()[0] if cmd else ""
        return (
            first in direct_cmds or
            cmd.startswith("./") or
            cmd.startswith("/") or
            cmd.startswith("~/")
        )
    
    def prompt(self) -> str:
        """
        Generate the shell prompt string.
        
        Returns:
            Formatted prompt showing current directory and LLM status
        """
        cwd_short = self.cwd.replace(str(Path.home()), "~")
        if len(cwd_short) > 35:
            cwd_short = "..." + cwd_short[-32:]
        llm_status = "🧠" if self.llm_providers else "💤"
        return f"{llm_status} {cwd_short} ❯ "
    
    async def run(self) -> None:
        """
        Main async REPL (Read-Eval-Print Loop).
        
        Runs the interactive shell until user exits.
        """
        llm_name = self.llm_providers[0].name if self.llm_providers else "none"
        print(f"🚀 ASTRO Vibe Shell (LLM: {llm_name})")
        print(f"📂 {self.cwd}")
        print("Type naturally or 'help' for examples\n")
        
        while True:
            try:
                user_input = input(self.prompt()).strip()
                if not user_input:
                    continue
                
                # Built-in?
                result = await self.handle_builtin(user_input)
                if result is not None:
                    if result:
                        print(result)
                    continue
                
                # Direct shell command?
                if self.is_direct_command(user_input):
                    print(await self.tool_shell(user_input))
                    continue
                
                # Natural language -> ReAct
                print()  # Spacing
                response = await self.react(user_input)
                print(f"\n✨ {response}\n")
                
            except KeyboardInterrupt:
                print("\n(Ctrl+C - use 'exit' to quit)")
            except EOFError:
                await self.cleanup()
                print("\n👋 Bye!")
                break
            except Exception as e:
                logger.exception("Error in main loop")
                print(f"\n❌ Error: {e}\n")


async def main() -> None:
    """Entry point for running VibeShell."""
    shell = VibeShell()
    try:
        await shell.initialize()
        await shell.run()
    finally:
        await shell.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
