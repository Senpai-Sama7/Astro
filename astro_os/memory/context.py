"""Memory - Recursive context loader and persistent state."""

import os
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
from datetime import datetime


@dataclass
class ProjectContext:
    """Indexed project context."""
    path: str
    name: str
    readme: str = ""
    package_json: Dict[str, Any] = field(default_factory=dict)
    structure: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    indexed_at: str = ""


@dataclass
class SessionState:
    """Persistent session state."""
    session_id: str
    created_at: str
    cwd: str
    mode: str = "shell"  # shell or web
    conversation: List[Dict[str, str]] = field(default_factory=list)
    project_contexts: Dict[str, ProjectContext] = field(default_factory=dict)
    command_history: List[str] = field(default_factory=list)
    browser_history: List[str] = field(default_factory=list)


class Memory:
    """Recursive context loader with persistent state."""
    
    STATE_FILE = Path.home() / ".astro_os_state.json"
    MAX_CONVERSATION = 50
    MAX_FILE_SIZE = 100_000  # 100KB max for file indexing
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_session_id()
        self.state = self._load_or_create_state()
    
    def _generate_session_id(self) -> str:
        return hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
    
    def _load_or_create_state(self) -> SessionState:
        """Load existing state or create new."""
        if self.STATE_FILE.exists():
            try:
                with open(self.STATE_FILE) as f:
                    data = json.load(f)
                    # Reconstruct ProjectContext objects
                    contexts = {}
                    for k, v in data.get("project_contexts", {}).items():
                        contexts[k] = ProjectContext(**v)
                    data["project_contexts"] = contexts
                    return SessionState(**data)
            except Exception:
                pass
        
        return SessionState(
            session_id=self.session_id,
            created_at=datetime.now().isoformat(),
            cwd=os.getcwd()
        )
    
    def save(self):
        """Persist state to disk."""
        data = asdict(self.state)
        # Trim conversation to prevent bloat
        data["conversation"] = data["conversation"][-self.MAX_CONVERSATION:]
        data["command_history"] = data["command_history"][-100:]
        
        with open(self.STATE_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        self.state.conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save()
    
    def add_command(self, command: str):
        """Add command to history."""
        self.state.command_history.append(command)
        self.save()
    
    def get_conversation(self, limit: int = 20) -> List[Dict[str, str]]:
        """Get recent conversation for context."""
        return self.state.conversation[-limit:]
    
    def set_mode(self, mode: str):
        """Set current mode (shell/web)."""
        self.state.mode = mode
        self.save()
    
    def set_cwd(self, cwd: str):
        """Update current working directory."""
        self.state.cwd = cwd
        self.save()
    
    def index_project(self, path: str) -> ProjectContext:
        """Recursively index a project directory."""
        path = os.path.abspath(os.path.expanduser(path))
        
        if path in self.state.project_contexts:
            ctx = self.state.project_contexts[path]
            # Re-index if older than 1 hour
            if ctx.indexed_at:
                indexed = datetime.fromisoformat(ctx.indexed_at)
                if (datetime.now() - indexed).seconds < 3600:
                    return ctx
        
        ctx = ProjectContext(
            path=path,
            name=os.path.basename(path),
            indexed_at=datetime.now().isoformat()
        )
        
        # Read README
        for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
            readme_path = os.path.join(path, readme_name)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read(self.MAX_FILE_SIZE)
                        ctx.readme = content[:5000]  # Limit for context
                    break
                except:
                    pass
        
        # Read package.json / pyproject.toml
        pkg_path = os.path.join(path, "package.json")
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path) as f:
                    ctx.package_json = json.load(f)
                ctx.languages.append("javascript")
            except:
                pass
        
        pyproject = os.path.join(path, "pyproject.toml")
        if os.path.exists(pyproject):
            ctx.languages.append("python")
        
        requirements = os.path.join(path, "requirements.txt")
        if os.path.exists(requirements):
            ctx.languages.append("python")
        
        cargo = os.path.join(path, "Cargo.toml")
        if os.path.exists(cargo):
            ctx.languages.append("rust")
        
        # Build structure (limited depth)
        ctx.structure = self._scan_structure(path, max_depth=3, max_files=100)
        
        self.state.project_contexts[path] = ctx
        self.save()
        return ctx
    
    def _scan_structure(self, path: str, max_depth: int = 3, max_files: int = 100, 
                       current_depth: int = 0, prefix: str = "") -> List[str]:
        """Scan directory structure."""
        if current_depth >= max_depth:
            return []
        
        result = []
        try:
            items = sorted(os.listdir(path))
            # Filter out common noise
            items = [i for i in items if not i.startswith(".") and i not in 
                    ["node_modules", "__pycache__", "venv", ".venv", "dist", "build", 
                     "target", ".git", "coverage", ".next", ".cache"]]
            
            for i, item in enumerate(items[:max_files]):
                item_path = os.path.join(path, item)
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                
                if os.path.isdir(item_path):
                    result.append(f"{prefix}{connector}{item}/")
                    extension = "    " if is_last else "│   "
                    result.extend(self._scan_structure(
                        item_path, max_depth, max_files, 
                        current_depth + 1, prefix + extension
                    ))
                else:
                    result.append(f"{prefix}{connector}{item}")
                
                if len(result) >= max_files:
                    break
        except PermissionError:
            pass
        
        return result
    
    def get_project_context(self, path: Optional[str] = None) -> Optional[ProjectContext]:
        """Get indexed project context."""
        path = path or self.state.cwd
        path = os.path.abspath(path)
        
        # Check if we have this path or any parent indexed
        for indexed_path in self.state.project_contexts:
            if path.startswith(indexed_path):
                return self.state.project_contexts[indexed_path]
        
        return None
    
    def build_context_prompt(self) -> str:
        """Build context string for LLM."""
        parts = [f"Session: {self.state.session_id}", f"CWD: {self.state.cwd}", f"Mode: {self.state.mode}"]
        
        # Add project context if available
        ctx = self.get_project_context()
        if ctx:
            parts.append(f"\n## Project: {ctx.name}")
            if ctx.readme:
                parts.append(f"README (excerpt):\n{ctx.readme[:2000]}")
            if ctx.package_json:
                deps = ctx.package_json.get("dependencies", {})
                parts.append(f"Dependencies: {', '.join(list(deps.keys())[:20])}")
            if ctx.structure:
                parts.append(f"Structure:\n" + "\n".join(ctx.structure[:50]))
        
        return "\n".join(parts)
    
    def clear(self):
        """Clear session state."""
        self.state = SessionState(
            session_id=self._generate_session_id(),
            created_at=datetime.now().isoformat(),
            cwd=os.getcwd()
        )
        self.save()
