"""Shell Tool - Self-healing command execution with sudo escalation."""

import os
import asyncio
import subprocess
import shlex
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable
from datetime import datetime


@dataclass
class ShellResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    cwd: str
    duration: float
    suggested_fix: Optional[str] = None
    needs_sudo: bool = False


# Patterns that indicate permission issues
PERMISSION_PATTERNS = [
    "permission denied",
    "operation not permitted",
    "access denied",
    "must be root",
    "requires root",
    "run as root",
    "need to be root",
    "insufficient privileges",
]

# Commands that typically need sudo on Kali/security distros
SUDO_COMMANDS = [
    "nmap", "masscan", "airmon-ng", "airodump-ng", "aireplay-ng",
    "tcpdump", "wireshark", "ettercap", "arpspoof", "macchanger",
    "systemctl", "service", "apt", "dpkg", "mount", "umount",
    "iptables", "ufw", "netstat", "ss", "lsof",
]


class ShellTool:
    """Self-healing shell executor with sudo escalation support."""
    
    def __init__(self, cwd: Optional[str] = None, log_callback: Optional[Callable[[str], Awaitable[None]]] = None):
        self.cwd = cwd or os.getcwd()
        self.log_callback = log_callback
        self.history: list[ShellResult] = []
        self.env = os.environ.copy()
        self.env["TERM"] = "xterm-256color"
    
    async def log(self, msg: str):
        if self.log_callback:
            await self.log_callback(msg)
    
    def _needs_sudo(self, command: str, stderr: str) -> bool:
        """Check if command needs sudo based on error or command type."""
        cmd_parts = shlex.split(command)
        base_cmd = cmd_parts[0] if cmd_parts else ""
        
        # Check if it's a known sudo command
        if base_cmd in SUDO_COMMANDS:
            return True
        
        # Check error patterns
        stderr_lower = stderr.lower()
        return any(p in stderr_lower for p in PERMISSION_PATTERNS)
    
    def _suggest_fix(self, command: str, stderr: str) -> Optional[str]:
        """Suggest a fix for failed commands."""
        if self._needs_sudo(command, stderr):
            if not command.strip().startswith("sudo"):
                return f"sudo {command}"
        
        # Package not found
        if "command not found" in stderr.lower() or "not found" in stderr.lower():
            cmd = shlex.split(command)[0] if command else ""
            return f"sudo apt install {cmd}  # Install missing package"
        
        # File not found
        if "no such file or directory" in stderr.lower():
            return "# Check if the file/path exists"
        
        return None
    
    async def execute(self, command: str, timeout: int = 300, allow_sudo: bool = False) -> ShellResult:
        """Execute command with self-healing capabilities."""
        await self.log(f"[SHELL] $ {command}")
        start = datetime.now()
        
        # Handle cd specially
        if command.strip().startswith("cd "):
            new_dir = command.strip()[3:].strip()
            new_dir = os.path.expanduser(new_dir)
            if not os.path.isabs(new_dir):
                new_dir = os.path.join(self.cwd, new_dir)
            new_dir = os.path.normpath(new_dir)
            
            if os.path.isdir(new_dir):
                self.cwd = new_dir
                result = ShellResult(command, 0, f"Changed to {new_dir}", "", self.cwd, 0.0)
            else:
                result = ShellResult(command, 1, "", f"No such directory: {new_dir}", self.cwd, 0.0)
            
            await self.log(f"[SHELL] → {result.stdout or result.stderr}")
            self.history.append(result)
            return result
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd,
                env=self.env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                result = ShellResult(command, -1, "", "Command timed out", self.cwd, timeout)
                self.history.append(result)
                return result
            
            duration = (datetime.now() - start).total_seconds()
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            result = ShellResult(
                command=command,
                exit_code=proc.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
                cwd=self.cwd,
                duration=duration
            )
            
            # Self-healing: suggest fixes for failures
            if result.exit_code != 0:
                result.needs_sudo = self._needs_sudo(command, stderr_str)
                result.suggested_fix = self._suggest_fix(command, stderr_str)
                await self.log(f"[SHELL] ✗ Exit {result.exit_code}")
                if result.suggested_fix:
                    await self.log(f"[SHELL] 💡 Suggested: {result.suggested_fix}")
            else:
                await self.log(f"[SHELL] ✓ Done ({duration:.2f}s)")
            
            # Log output preview
            if stdout_str:
                preview = stdout_str[:200] + "..." if len(stdout_str) > 200 else stdout_str
                await self.log(f"[SHELL] {preview.strip()}")
            
            self.history.append(result)
            return result
            
        except Exception as e:
            result = ShellResult(command, -1, "", str(e), self.cwd, 0.0)
            self.history.append(result)
            await self.log(f"[SHELL] Error: {e}")
            return result
    
    async def execute_with_healing(self, command: str, max_retries: int = 2) -> ShellResult:
        """Execute with automatic retry using suggested fixes."""
        result = await self.execute(command)
        
        retries = 0
        while result.exit_code != 0 and result.suggested_fix and retries < max_retries:
            await self.log(f"[SHELL] Attempting self-heal with: {result.suggested_fix}")
            # Don't auto-execute sudo - just suggest
            if result.needs_sudo:
                break
            result = await self.execute(result.suggested_fix)
            retries += 1
        
        return result
