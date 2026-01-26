"""Shell Executor - Claude Code Mode with deep project indexing and self-healing."""

import os
import asyncio
import subprocess
import shutil
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json


@dataclass
class ExecutionResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    cwd: str
    duration: float
    success: bool = field(init=False)
    suggested_fix: Optional[str] = None
    rca: Optional[str] = None  # Root Cause Analysis
    
    def __post_init__(self):
        self.success = self.exit_code == 0


@dataclass 
class ProjectIndex:
    """Deep project index for Claude Code mode."""
    path: str
    name: str
    readme: str = ""
    package_json: Dict[str, Any] = field(default_factory=dict)
    pyproject: Dict[str, Any] = field(default_factory=dict)
    structure: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    config_files: Dict[str, str] = field(default_factory=dict)
    indexed_at: str = ""


# Error patterns for RCA
ERROR_PATTERNS = {
    "permission denied": {"rca": "Insufficient permissions", "fix": "sudo {cmd}"},
    "command not found": {"rca": "Command not installed", "fix": "sudo apt install {pkg}"},
    "no such file": {"rca": "File/directory doesn't exist", "fix": "mkdir -p {path}"},
    "connection refused": {"rca": "Service not running", "fix": "sudo systemctl start {service}"},
    "port already in use": {"rca": "Port conflict", "fix": "sudo lsof -i :{port} && kill -9 {pid}"},
    "module not found": {"rca": "Python module missing", "fix": "pip install {module}"},
    "eacces": {"rca": "Access denied", "fix": "chmod +x {file}"},
    "enomem": {"rca": "Out of memory", "fix": "free -h && sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches"},
}

# Kali tools that need sudo
KALI_SUDO_TOOLS = [
    "nmap", "masscan", "airmon-ng", "airodump-ng", "aireplay-ng", "aircrack-ng",
    "tcpdump", "wireshark", "tshark", "ettercap", "arpspoof", "macchanger",
    "hydra", "john", "hashcat", "sqlmap", "nikto", "dirb", "gobuster",
    "metasploit", "msfconsole", "msfvenom", "setoolkit", "beef-xss",
    "burpsuite", "zaproxy", "wpscan", "enum4linux", "smbclient",
    "netcat", "nc", "socat", "proxychains", "tor",
]


class ShellExecutor:
    """Self-healing shell executor with deep project indexing."""
    
    def __init__(self, cwd: Optional[str] = None, 
                 log_callback: Optional[Callable[[str], Awaitable[None]]] = None,
                 llm_callback: Optional[Callable[[str], Awaitable[str]]] = None):
        self.cwd = cwd or os.getcwd()
        self.log = log_callback or self._default_log
        self.llm = llm_callback  # For intelligent RCA
        self.history: List[ExecutionResult] = []
        self.project_index: Optional[ProjectIndex] = None
        self.env = os.environ.copy()
        self.env["TERM"] = "xterm-256color"
        self.kali_tools = self._detect_kali_tools()
    
    async def _default_log(self, msg: str):
        print(f"[SHELL] {msg}")
    
    def _detect_kali_tools(self) -> Dict[str, str]:
        """Detect available Kali tools."""
        tools = {}
        for tool in KALI_SUDO_TOOLS:
            path = shutil.which(tool)
            if path:
                tools[tool] = path
        return tools
    
    def _needs_sudo(self, command: str) -> bool:
        """Check if command needs sudo."""
        parts = command.split()
        if not parts:
            return False
        base_cmd = parts[0]
        return base_cmd in KALI_SUDO_TOOLS or base_cmd in self.kali_tools
    
    def _perform_rca(self, command: str, stderr: str) -> tuple[str, Optional[str]]:
        """Perform Root Cause Analysis on error."""
        stderr_lower = stderr.lower()
        
        for pattern, info in ERROR_PATTERNS.items():
            if pattern in stderr_lower:
                rca = info["rca"]
                fix_template = info["fix"]
                
                # Try to construct fix
                parts = command.split()
                fix = None
                if "{cmd}" in fix_template:
                    fix = fix_template.format(cmd=command)
                elif "{pkg}" in fix_template and parts:
                    fix = fix_template.format(pkg=parts[0])
                
                return rca, fix
        
        # Check for sudo need
        if self._needs_sudo(command) and not command.strip().startswith("sudo"):
            return "Command requires elevated privileges", f"sudo {command}"
        
        return "Unknown error", None
    
    async def execute(self, command: str, timeout: int = 300) -> ExecutionResult:
        """Execute command with logging."""
        await self.log(f"$ {command}")
        start = datetime.now()
        
        # Handle cd specially
        if command.strip().startswith("cd "):
            return await self._handle_cd(command)
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd,
                env=self.env
            )
            
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            duration = (datetime.now() - start).total_seconds()
            
            result = ExecutionResult(
                command=command,
                exit_code=proc.returncode or 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                cwd=self.cwd,
                duration=duration
            )
            
            if not result.success:
                result.rca, result.suggested_fix = self._perform_rca(command, result.stderr)
                await self.log(f"✗ Exit {result.exit_code} | RCA: {result.rca}")
                if result.suggested_fix:
                    await self.log(f"💡 Fix: {result.suggested_fix}")
            else:
                await self.log(f"✓ Done ({duration:.2f}s)")
            
            self.history.append(result)
            return result
            
        except asyncio.TimeoutError:
            return ExecutionResult(command, -1, "", "Timeout", self.cwd, timeout, rca="Command timed out")
        except Exception as e:
            return ExecutionResult(command, -1, "", str(e), self.cwd, 0, rca=str(e))
    
    async def _handle_cd(self, command: str) -> ExecutionResult:
        """Handle cd command."""
        new_dir = command.strip()[3:].strip()
        new_dir = os.path.expanduser(new_dir)
        if not os.path.isabs(new_dir):
            new_dir = os.path.join(self.cwd, new_dir)
        new_dir = os.path.normpath(new_dir)
        
        if os.path.isdir(new_dir):
            self.cwd = new_dir
            await self.log(f"→ {new_dir}")
            return ExecutionResult(command, 0, f"Changed to {new_dir}", "", self.cwd, 0)
        else:
            return ExecutionResult(command, 1, "", f"No such directory: {new_dir}", self.cwd, 0,
                                  rca="Directory doesn't exist", suggested_fix=f"mkdir -p {new_dir}")
    
    async def execute_with_healing(self, command: str, max_retries: int = 3) -> ExecutionResult:
        """Execute with self-healing retry loop."""
        result = await self.execute(command)
        retries = 0
        
        while not result.success and result.suggested_fix and retries < max_retries:
            # Don't auto-execute sudo without confirmation
            if "sudo" in result.suggested_fix and "sudo" not in command:
                await self.log(f"⚠️ Needs sudo - awaiting confirmation")
                break
            
            await self.log(f"🔄 Self-heal attempt {retries + 1}/{max_retries}")
            result = await self.execute(result.suggested_fix)
            retries += 1
        
        return result
    
    async def index_project(self, path: Optional[str] = None) -> ProjectIndex:
        """Deep index a project directory (Claude Code mode)."""
        path = os.path.abspath(path or self.cwd)
        await self.log(f"📂 Indexing project: {path}")
        
        index = ProjectIndex(
            path=path,
            name=os.path.basename(path),
            indexed_at=datetime.now().isoformat()
        )
        
        # Read README
        for name in ["README.md", "README.rst", "README.txt", "README"]:
            readme_path = os.path.join(path, name)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, encoding="utf-8", errors="ignore") as f:
                        index.readme = f.read(50000)[:8000]
                    break
                except: pass
        
        # Read package.json
        pkg_path = os.path.join(path, "package.json")
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path) as f:
                    index.package_json = json.load(f)
                index.languages.append("javascript/typescript")
                if "main" in index.package_json:
                    index.entry_points.append(index.package_json["main"])
            except: pass
        
        # Read pyproject.toml
        pyproject_path = os.path.join(path, "pyproject.toml")
        if os.path.exists(pyproject_path):
            index.languages.append("python")
            try:
                with open(pyproject_path) as f:
                    index.config_files["pyproject.toml"] = f.read(10000)
            except: pass
        
        # Read requirements.txt
        req_path = os.path.join(path, "requirements.txt")
        if os.path.exists(req_path):
            index.languages.append("python")
            try:
                with open(req_path) as f:
                    index.config_files["requirements.txt"] = f.read(5000)
            except: pass
        
        # Read Cargo.toml
        cargo_path = os.path.join(path, "Cargo.toml")
        if os.path.exists(cargo_path):
            index.languages.append("rust")
            try:
                with open(cargo_path) as f:
                    index.config_files["Cargo.toml"] = f.read(5000)
            except: pass
        
        # Build structure
        index.structure = self._scan_tree(path)
        
        # Find entry points
        for pattern in ["main.py", "app.py", "index.js", "index.ts", "main.rs", "src/main.*"]:
            for item in Path(path).rglob(pattern.replace("*", "**")):
                if "__pycache__" not in str(item) and "node_modules" not in str(item):
                    index.entry_points.append(str(item.relative_to(path)))
        
        self.project_index = index
        await self.log(f"✓ Indexed: {len(index.structure)} items, {len(index.languages)} languages")
        return index
    
    def _scan_tree(self, path: str, max_depth: int = 4, max_items: int = 150) -> List[str]:
        """Scan directory tree."""
        result = []
        skip = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", 
                "target", "coverage", ".next", ".cache", ".pytest_cache", "*.pyc"}
        
        def scan(p: str, depth: int, prefix: str):
            if depth > max_depth or len(result) >= max_items:
                return
            try:
                items = sorted(os.listdir(p))
                items = [i for i in items if not any(i == s or (s.startswith("*") and i.endswith(s[1:])) for s in skip)]
                
                for i, item in enumerate(items):
                    if len(result) >= max_items:
                        break
                    item_path = os.path.join(p, item)
                    is_last = i == len(items) - 1
                    connector = "└── " if is_last else "├── "
                    
                    if os.path.isdir(item_path):
                        result.append(f"{prefix}{connector}{item}/")
                        scan(item_path, depth + 1, prefix + ("    " if is_last else "│   "))
                    else:
                        result.append(f"{prefix}{connector}{item}")
            except PermissionError:
                pass
        
        scan(path, 0, "")
        return result
    
    def get_context(self) -> str:
        """Get current context for LLM."""
        parts = [f"CWD: {self.cwd}"]
        
        if self.kali_tools:
            parts.append(f"Kali Tools: {', '.join(list(self.kali_tools.keys())[:20])}")
        
        if self.project_index:
            parts.append(f"\n## Project: {self.project_index.name}")
            parts.append(f"Languages: {', '.join(self.project_index.languages)}")
            if self.project_index.readme:
                parts.append(f"README:\n{self.project_index.readme[:3000]}")
            if self.project_index.structure:
                parts.append(f"Structure:\n" + "\n".join(self.project_index.structure[:60]))
        
        return "\n".join(parts)
