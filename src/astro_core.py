"""
ASTRO Core - Unified interface for all ASTRO capabilities.

This module integrates:
- Universal LLM providers (OpenAI, Anthropic, Google, OpenRouter, Ollama, llama.cpp)
- Skills system with self-modification
- Browser automation
- Computer use (mouse/keyboard)
- Live canvas/UI
- Task scheduler
- Telegram bot
- MCP client
- Sub-agent orchestration
"""

import asyncio
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .llm import LLMFactory, LLMProvider
from .skills import SkillManager, SkillContext
from .canvas import CanvasManager, CanvasServer
from .computer import ComputerController, ScreenVision
from .channels import TelegramBot
from .mcp import MCPClient
from .agents import AgentOrchestrator


logger = logging.getLogger("ASTRO.Core")

class AstroCore:
    """
    Main ASTRO Core - Your AI assistant with superpowers.
    
    Usage:
        astro = AstroCore()
        await astro.initialize()
        
        # Use LLM
        response = await astro.llm.complete([{"role": "user", "content": "Hello"}])
        
        # Use skills
        result = await astro.skills.execute_skill("file", {"action": "list", "path": "."}, context)
        
        # Create canvas
        canvas = astro.canvas.create("My Workspace")
        
        # Control computer
        await astro.computer.execute("click", x=100, y=200)
        
        # Spawn sub-agents
        task = await astro.agents.submit_task("Analyze this code", agent_type="code")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core components
        self.llm: Optional[LLMProvider] = None
        self.skills: Optional[SkillManager] = None
        self.canvas: Optional[CanvasManager] = None
        self.computer: Optional[ComputerController] = None
        self.vision: Optional[ScreenVision] = None
        self.telegram: Optional[TelegramBot] = None
        self.mcp: Optional[MCPClient] = None
        self.agents: Optional[AgentOrchestrator] = None
        
        # Servers
        self.canvas_server: Optional[CanvasServer] = None
        
        # State
        self._initialized = False
        self._workspace_dir = Path(self.config.get("workspace", Path.home() / ".astro"))
    
    async def initialize(self):
        """Initialize all ASTRO components."""
        if self._initialized:
            return
        
        logger.info("🚀 Initializing ASTRO Core...")
        
        # 1. Initialize LLM provider
        await self._init_llm()
        
        # 2. Initialize skills system
        await self._init_skills()
        
        # 3. Initialize canvas
        await self._init_canvas()
        
        # 4. Initialize computer control
        await self._init_computer()
        
        # 5. Initialize MCP client
        await self._init_mcp()
        
        # 6. Initialize sub-agent orchestration
        await self._init_agents()
        
        # 7. Initialize Telegram bot (optional)
        await self._init_telegram()
        
        self._initialized = True
        logger.info("✅ ASTRO Core initialized successfully!")
    
    async def _init_llm(self):
        """Initialize LLM provider."""
        try:
            preferred = self.config.get("llm_priority")
            self.llm = await LLMFactory.create_with_fallback(preferred)
            logger.info(f"  🤖 LLM: {self.llm.name}")
        except Exception:
            logger.exception("  ⚠️  LLM initialization failed")
    
    async def _init_skills(self):
        """Initialize skills system."""
        self.skills = SkillManager(
            workspace_dir=self._workspace_dir / "skills",
            llm_provider=self.llm
        )
        await self.skills.initialize()
        
        # Set scheduler's skill manager
        scheduler = self.skills.registry.get("scheduler")
        if scheduler:
            scheduler.set_skill_manager(self.skills)
        
        logger.info(f"  🔧 Skills: {len(self.skills.registry.list_skills())} loaded")
    
    async def _init_canvas(self):
        """Initialize canvas system."""
        self.canvas = CanvasManager()
        
        # Start canvas WebSocket server
        canvas_port = self.config.get("canvas_port", 8765)
        self.canvas_server = CanvasServer(self.canvas, port=canvas_port)
        await self.canvas_server.start()
        
        logger.info(f"  🎨 Canvas: ws://localhost:{canvas_port}")
    
    async def _init_computer(self):
        """Initialize computer control."""
        self.computer = ComputerController()
        self.vision = ScreenVision()
        
        if self.computer.is_available():
            logger.info("  💻 Computer control: Available")
        else:
            logger.info("  💻 Computer control: Install pyautogui for full features")
    
    async def _init_mcp(self):
        """Initialize MCP client."""
        self.mcp = MCPClient()
        
        if self.mcp.is_available():
            logger.info("  🔌 MCP: Available")
            
            # Auto-connect to configured MCP servers
            mcp_servers = self.config.get("mcp_servers", {})
            for server_id, server_config in mcp_servers.items():
                try:
                    await self.mcp.connect_stdio(
                        server_id,
                        server_config["command"],
                        server_config.get("args", []),
                        server_config.get("env")
                    )
                except Exception:
                    logger.exception(f"    ⚠️  Failed to connect to MCP server '{server_id}'")
        else:
            logger.info("  🔌 MCP: Install mcp package for MCP support")
    
    async def _init_agents(self):
        """Initialize sub-agent orchestration."""
        self.agents = AgentOrchestrator(llm_provider=self.llm)
        
        # Create default agents
        self.agents.create_agent(
            name="Code Analyst",
            agent_type="code",
            system_prompt="You are a code analysis expert. Review code for bugs, security issues, and improvements."
        )
        
        self.agents.create_agent(
            name="Research Assistant",
            agent_type="research",
            system_prompt="You are a research assistant. Find information, summarize content, and answer questions."
        )
        
        self.agents.create_agent(
            name="File Manager",
            agent_type="files",
            system_prompt="You are a file management expert. Organize, search, and manage files efficiently."
        )
        
        logger.info(f"  🤖 Sub-agents: {len(self.agents.agents)} created")
    
    async def _init_telegram(self):
        """Initialize Telegram bot."""
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            self.telegram = TelegramBot(
                allowed_users=self.config.get("telegram_allowed_users"),
                skill_manager=self.skills,
                llm_provider=self.llm,
                canvas_manager=self.canvas,
                canvas_port=self.config.get("canvas_port", 8765)
            )
            await self.telegram.start()
            logger.info("  💬 Telegram bot: Active")
        else:
            logger.info("  💬 Telegram bot: Set TELEGRAM_BOT_TOKEN to enable")
    
    async def shutdown(self):
        """Shutdown all components."""
        logger.info("🛑 Shutting down ASTRO Core...")
        
        if self.canvas_server:
            await self.canvas_server.stop()
        
        if self.telegram:
            await self.telegram.stop()
        
        if self.mcp:
            await self.mcp.disconnect_all()
        
        self._initialized = False
        logger.info("✅ Shutdown complete")
    
    # ==================== High-Level API ====================
    
    async def chat(self, message: str, context: Optional[SkillContext] = None) -> str:
        """
        Main chat interface - the smart way to talk to ASTRO.
        
        This method:
        1. Understands the intent
        2. Routes to appropriate skill or LLM
        3. Returns a helpful response
        """
        if not self._initialized:
            return "ASTRO not initialized. Call initialize() first."
        
        # Create context if not provided
        if context is None:
            context = SkillContext(
                user_id="user",
                session_id="default",
                working_directory=str(Path.cwd()),
                llm_provider=self.llm
            )
        
        # Try to parse as skill command
        if message.startswith("/"):
            parts = message[1:].split(maxsplit=1)
            skill_name = parts[0]
            skill_input = parts[1] if len(parts) > 1 else "{}"
            
            try:
                import json
                params = json.loads(skill_input) if skill_input.startswith("{") else {"text": skill_input}
                result = await self.skills.execute_skill(skill_name, params, context)
                return result.message
            except Exception:
                return "❌ An error occurred while executing the skill. Please try again later."
        
        # Use LLM for general conversation
        if self.llm:
            try:
                response = await self.llm.complete([
                    {"role": "user", "content": message}
                ])
                return response.content
            except Exception:
                return "❌ An error occurred while generating a response. Please try again later."
        
        return "No LLM available. Please configure an LLM provider."
    
    async def execute_task(
        self,
        description: str,
        agent_type: str = "general",
        use_sub_agent: bool = False
    ) -> str:
        """
        Execute a task, optionally using a sub-agent.
        """
        if use_sub_agent and self.agents:
            task = await self.agents.submit_task(description, agent_type)
            
            # Wait for completion
            while not task.is_done:
                await asyncio.sleep(0.1)
            
            if task.result and task.result.success:
                return str(task.result.output)
            else:
                return f"Task failed: {task.result.error if task.result else 'Unknown error'}"
        else:
            # Execute directly via LLM
            if self.llm:
                response = await self.llm.complete([
                    {"role": "system", "content": f"You are ASTRO. Execute this task: {description}"},
                    {"role": "user", "content": description}
                ])
                return response.content
            
            return "No execution method available"
    
    def create_canvas(self, title: str = "ASTRO Canvas") -> Any:
        """Create a new live canvas."""
        return self.canvas.create(title)
    
    async def browser_goto(self, url: str) -> str:
        """Navigate browser to URL."""
        if not self.skills:
            return "Skills not available"
        
        context = SkillContext(
            user_id="user",
            session_id="browser",
            working_directory=str(Path.cwd())
        )
        
        result = await self.skills.execute_skill(
            "browser",
            {"action": "goto", "url": url},
            context
        )
        
        return result.message
    
    async def schedule_task(
        self,
        name: str,
        schedule: str,  # cron expression or @daily/@hourly
        skill_name: str,
        skill_params: Optional[Dict] = None
    ) -> str:
        """Schedule a recurring task."""
        if not self.skills:
            return "Skills not available"
        
        context = SkillContext(
            user_id="user",
            session_id="scheduler",
            working_directory=str(Path.cwd())
        )
        
        result = await self.skills.execute_skill(
            "scheduler",
            {
                "action": "add",
                "name": name,
                "schedule": schedule,
                "skill_name": skill_name,
                "skill_params": skill_params or {}
            },
            context
        )
        
        return result.message
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            "initialized": self._initialized,
            "llm": self.llm.name if self.llm else None,
            "skills": len(self.skills.registry.list_skills()) if self.skills else 0,
            "canvases": len(self.canvas.list_canvases()) if self.canvas else 0,
            "agents": len(self.agents.agents) if self.agents else 0,
            "mcp_servers": len(self.mcp.sessions) if self.mcp else 0,
            "telegram": self.telegram.is_available() if self.telegram else False,
            "computer_control": self.computer.is_available() if self.computer else False,
        }
