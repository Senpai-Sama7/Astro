#!/usr/bin/env python3
"""
ASTRO Core CLI - Command-line interface for the enhanced ASTRO.

Usage:
    python astro_core_cli.py
    python astro_core_cli.py "create a skill that fetches weather"
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.astro_core import AstroCore
from src.skills import SkillContext


class AstroCoreCLI:
    """Interactive CLI for ASTRO Core."""
    
    def __init__(self):
        self.astro = None
        self.session_id = "cli_session"
    
    async def initialize(self):
        """Initialize ASTRO Core."""
        config = {
            "workspace": Path.home() / ".astro",
            "canvas_port": 8765,
            "llm_priority": ["ollama", "anthropic", "openai", "openrouter"]
        }
        
        self.astro = AstroCore(config)
        await self.astro.initialize()
    
    async def run_interactive(self):
        """Run interactive mode."""
        print("\n" + "="*50)
        print("🚀 ASTRO Core - Enhanced AI Assistant")
        print("="*50)
        print("\nCommands:")
        print("  /skills        - List available skills")
        print("  /status        - Show system status")
        print("  /canvas        - Create a new canvas")
        print("  /agents        - List sub-agents")
        print("  /browser <url> - Open browser")
        print("  /schedule ...  - Schedule a task")
        print("  /quit          - Exit")
        print("\nOr just type naturally and I'll help you!\n")
        
        while True:
            try:
                user_input = input("🤖 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                if user_input == '/status':
                    status = self.astro.get_status()
                    print("\n📊 System Status:")
                    for key, value in status.items():
                        print(f"  {key}: {value}")
                    print()
                    continue
                
                if user_input == '/skills':
                    if self.astro.skills:
                        help_text = self.astro.skills.get_skill_help()
                        print(f"\n{help_text}\n")
                    continue
                
                if user_input == '/agents':
                    if self.astro.agents:
                        print("\n🤖 Sub-Agents:")
                        for agent_id, agent in self.astro.agents.agents.items():
                            print(f"  {agent.name} ({agent.agent_type}) - ID: {agent_id}")
                    print()
                    continue
                
                if user_input.startswith('/browser '):
                    url = user_input[9:].strip()
                    result = await self.astro.browser_goto(url)
                    print(f"\n🌐 {result}\n")
                    continue
                
                if user_input == '/canvas':
                    canvas = self.astro.create_canvas("CLI Canvas")
                    print(f"\n🎨 Canvas created: {canvas.id}")
                    print(f"   Open: http://localhost:8765/{canvas.id}\n")
                    continue
                
                # Process through main chat
                context = SkillContext(
                    user_id="cli_user",
                    session_id=self.session_id,
                    working_directory=str(Path.cwd()),
                    llm_provider=self.astro.llm
                )
                
                response = await self.astro.chat(user_input, context)
                print(f"\n🤖 ASTRO: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
    
    async def run_single(self, command: str):
        """Run a single command."""
        await self.initialize()
        
        context = SkillContext(
            user_id="cli_user",
            session_id=self.session_id,
            working_directory=str(Path.cwd()),
            llm_provider=self.astro.llm
        )
        
        response = await self.astro.chat(command, context)
        print(response)
    
    async def shutdown(self):
        """Cleanup."""
        if self.astro:
            await self.astro.shutdown()


async def main():
    """Main entry point."""
    cli = AstroCoreCLI()
    
    try:
async def run_single(self, command: str):
    """Run a single command."""
    
    context = SkillContext(
        user_id="cli_user",
        session_id=self.session_id,
        working_directory=str(Path.cwd()),
        llm_provider=self.astro.llm
    )
    
    response = await self.astro.chat(command, context)
    print(response)
        else:
            # Interactive mode
            await cli.run_interactive()
    
    finally:
        await cli.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
