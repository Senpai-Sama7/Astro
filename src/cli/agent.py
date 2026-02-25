#!/usr/bin/env python3
"""
ASTRO-CLI: Plan-and-Execute Terminal Assistant

A CLI agent that transforms natural language into executable shell commands
with user confirmation and result feedback.
"""

import os
import json
import subprocess
import platform
import getpass
from typing import Optional, Dict, Any, List

# Try to import colorama for cross-platform colors
try:
    from colorama import init, Fore, Style
    init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        RED = YELLOW = GREEN = CYAN = BLUE = MAGENTA = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""

# Try to import requests or httpx
try:
    import httpx
    HTTP_CLIENT = "httpx"
except ImportError:
    try:
        import requests
        HTTP_CLIENT = "requests"
    except ImportError:
        HTTP_CLIENT = None

from .prompts import CLI_AGENT_SYSTEM_PROMPT, RESULT_INJECTION_TEMPLATE

# Import shared agent


class AstroCLI:
    """Plan-and-Execute CLI Agent."""
    
    def __init__(self, api_url: str = "http://localhost:5000", api_key: Optional[str] = None):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key or os.environ.get("ASTRO_API_KEY", "")
        self.cwd = os.getcwd()
        self.conversation_history: List[Dict[str, str]] = []
        self.os_info = self._detect_os()
        self.shell = os.environ.get("SHELL", "/bin/bash")
        self.user = getpass.getuser()
        
    def _detect_os(self) -> str:
        """Detect OS and distribution."""
        system = platform.system()
        if system == "Linux":
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=")[1].strip().strip('"')
            except Exception:
                pass
            return f"Linux {platform.release()}"
        return f"{system} {platform.release()}"
    
    def _get_dir_contents(self, max_items: int = 50) -> str:
        """Get current directory contents."""
        try:
            items = sorted(os.listdir(self.cwd))[:max_items]
            dirs = [f"{d}/" for d in items if os.path.isdir(os.path.join(self.cwd, d))]
            files = [f for f in items if os.path.isfile(os.path.join(self.cwd, f))]
            
            result = []
            if dirs:
                result.append(f"Directories: {', '.join(dirs[:20])}")
            if files:
                result.append(f"Files: {', '.join(files[:30])}")
            if len(items) >= max_items:
                result.append(f"... and more ({len(os.listdir(self.cwd))} total items)")
            return "\n".join(result) if result else "(empty directory)"
        except Exception as e:
            return f"(error reading directory: {e})"
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with current context."""
        return CLI_AGENT_SYSTEM_PROMPT.format(
            os_info=self.os_info,
            cwd=self.cwd,
            dir_contents=self._get_dir_contents(),
            shell=self.shell,
            user=self.user
        )
    
    def _call_api(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call the Astro API or use local LLM."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "messages": messages,
            "context": {
                "cwd": self.cwd,
                "os": self.os_info,
                "user": self.user
            }
        }
        
        try:
            if HTTP_CLIENT == "httpx":
                with httpx.Client(timeout=60) as client:
                    resp = client.post(
                        f"{self.api_url}/api/v1/cli/chat",
                        json=payload,
                        headers=headers
                    )
                    resp.raise_for_status()
                    return resp.json().get("response", resp.text)
            elif HTTP_CLIENT == "requests":
                resp = requests.post(
                    f"{self.api_url}/api/v1/cli/chat",
                    json=payload,
                    headers=headers,
                    timeout=60
                )
                resp.raise_for_status()
                return resp.json().get("response", resp.text)
            else:
                # Fallback: use OpenAI directly if available
                return self._call_openai_direct(messages)
        except Exception as e:
            print(f"{Fore.RED}API Error: {e}{Style.RESET_ALL}")
            return None
    
    def _call_openai_direct(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Direct OpenAI call as fallback."""
        try:
            from openai import OpenAI
            client = OpenAI()
            response = client.chat.completions.create(
                model=os.environ.get("ASTRO_MODEL", "gpt-4o-mini"),
                messages=messages,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except ImportError:
            print(f"{Fore.RED}No HTTP client or OpenAI SDK available{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}OpenAI Error: {e}{Style.RESET_ALL}")
            return None
    
    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from agent."""
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code blocks
                lines = response.split("\n")
                response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"{Fore.YELLOW}Warning: Could not parse JSON response{Style.RESET_ALL}")
            print(f"{Fore.DIM}{response[:500]}{Style.RESET_ALL}")
            return None
    
    def _confirm_execution(self, command: str, dangerous: bool = False) -> bool:
        """Ask user for confirmation before executing."""
        color = Fore.RED if dangerous else Fore.YELLOW
        label = "⚠️  DANGEROUS" if dangerous else "Command"
        
        print(f"\n{color}{label}:{Style.RESET_ALL} {Fore.CYAN}{command}{Style.RESET_ALL}")
        
        if dangerous:
            print(f"{Fore.RED}This command may cause irreversible changes!{Style.RESET_ALL}")
        
        try:
            response = input(f"{Fore.GREEN}Execute? [y/N/e(dit)]: {Style.RESET_ALL}").strip().lower()
            if response == 'e':
                edited = input(f"{Fore.CYAN}Edit command: {Style.RESET_ALL}")
                return self._confirm_execution(edited.strip() or command, dangerous)
            return response in ('y', 'yes')
        except (KeyboardInterrupt, EOFError):
            print()
            return False
    
    def _execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a shell command and capture output."""
        try:
            # Use shlex to safely parse command for shell=False
            import shlex
            args = shlex.split(command)
            result = subprocess.run(
                args,
                shell=False,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=300,
                env={**os.environ, "TERM": "dumb"}
            )
            
            # Handle cd commands specially
            if command.strip().startswith("cd "):
                new_dir = command.strip()[3:].strip()
                if new_dir.startswith("~"):
                    new_dir = os.path.expanduser(new_dir)
                elif not new_dir.startswith("/"):
                    new_dir = os.path.join(self.cwd, new_dir)
                new_dir = os.path.normpath(new_dir)
                if os.path.isdir(new_dir):
                    self.cwd = new_dir
                    os.chdir(new_dir)
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "exit_code": -1, "stdout": "", "stderr": "Command timed out (300s)"}
        except Exception as e:
            return {"success": False, "exit_code": -1, "stdout": "", "stderr": str(e)}
    
    def _display_output(self, result: Dict[str, Any]):
        """Display command output."""
        if result["stdout"]:
            print(f"{Fore.WHITE}{result['stdout']}{Style.RESET_ALL}", end="")
        if result["stderr"]:
            print(f"{Fore.RED}{result['stderr']}{Style.RESET_ALL}", end="")
        
        status = f"{Fore.GREEN}✓" if result["success"] else f"{Fore.RED}✗ (exit {result['exit_code']})"
        print(f"\n{status}{Style.RESET_ALL}")
    
    def _inject_result(self, command: str, result: Dict[str, Any]):
        """Inject command result back into conversation."""
        injection = RESULT_INJECTION_TEMPLATE.format(
            command=command,
            exit_code=result["exit_code"],
            cwd=self.cwd,
            stdout=result["stdout"][:2000] if result["stdout"] else "(no output)",
            stderr=result["stderr"][:1000] if result["stderr"] else "(none)"
        )
        self.conversation_history.append({"role": "user", "content": injection})
    
    def chat(self, user_input: str) -> Optional[str]:
        """Process user input and return response."""
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Build messages with system prompt
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            *self.conversation_history[-20:]  # Keep last 20 messages for context
        ]
        
        # Call API
        response = self._call_api(messages)
        if not response:
            return None
        
        # Parse response
        parsed = self._parse_response(response)
        if not parsed:
            # If parsing fails, show raw response
            print(f"{Fore.CYAN}{response}{Style.RESET_ALL}")
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        # Add to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Display thought
        if "thought" in parsed:
            print(f"\n{Fore.BLUE}💭 {parsed['thought']}{Style.RESET_ALL}")
        
        # Handle info-only response
        if parsed.get("command") is None and "info" in parsed:
            print(f"\n{Fore.WHITE}{parsed['info']}{Style.RESET_ALL}")
            return response
        
        # Handle plan (multiple commands)
        if "plan" in parsed:
            print(f"\n{Fore.MAGENTA}📋 Plan with {len(parsed['plan'])} steps:{Style.RESET_ALL}")
            for step in parsed["plan"]:
                print(f"  {step['step']}. {step['description']}")
                print(f"     {Fore.DIM}{step['command']}{Style.RESET_ALL}")
            
            if input(f"\n{Fore.GREEN}Execute plan? [y/N]: {Style.RESET_ALL}").lower() in ('y', 'yes'):
                for step in parsed["plan"]:
                    print(f"\n{Fore.CYAN}Step {step['step']}: {step['description']}{Style.RESET_ALL}")
                    if self._confirm_execution(step["command"], parsed.get("dangerous", False)):
                        result = self._execute_command(step["command"])
                        self._display_output(result)
                        self._inject_result(step["command"], result)
                        if not result["success"]:
                            if input(f"{Fore.YELLOW}Continue despite error? [y/N]: {Style.RESET_ALL}").lower() not in ('y', 'yes'):
                                break
            return response
        
        # Handle single command
        if "command" in parsed and parsed["command"]:
            command = parsed["command"]
            dangerous = parsed.get("dangerous", False)
            
            if "description" in parsed:
                print(f"{Fore.DIM}→ {parsed['description']}{Style.RESET_ALL}")
            
            if self._confirm_execution(command, dangerous):
                result = self._execute_command(command)
                self._display_output(result)
                self._inject_result(command, result)
        
        return response
    
    def run(self):
        """Main REPL loop."""
        print(f"{Fore.CYAN}╔══════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL}  {Fore.WHITE}ASTRO-CLI{Style.RESET_ALL} - Plan-and-Execute Terminal Assistant      {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL}  Type 'exit' or Ctrl+C to quit, 'clear' to reset         {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        print(f"{Fore.DIM}OS: {self.os_info} | CWD: {self.cwd}{Style.RESET_ALL}\n")
        
        while True:
            try:
                # Show prompt with cwd
                cwd_display = self.cwd.replace(os.path.expanduser("~"), "~")
                user_input = input(f"{Fore.GREEN}astro{Style.RESET_ALL}:{Fore.BLUE}{cwd_display}{Style.RESET_ALL}$ ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ('exit', 'quit', 'q'):
                    print(f"{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                    break
                
                if user_input.lower() == 'clear':
                    self.conversation_history.clear()
                    print(f"{Fore.YELLOW}Conversation cleared.{Style.RESET_ALL}")
                    continue
                
                if user_input.lower() == 'history':
                    for i, msg in enumerate(self.conversation_history[-10:]):
                        role_color = Fore.GREEN if msg["role"] == "user" else Fore.CYAN
                        print(f"{role_color}[{msg['role']}]{Style.RESET_ALL} {msg['content'][:100]}...")
                    continue
                
                self.chat(user_input)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Use 'exit' to quit or press Ctrl+C again{Style.RESET_ALL}")
                try:
                    input()
                except KeyboardInterrupt:
                    print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                    break
            except EOFError:
                print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                break


def main():
    """Entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="ASTRO-CLI: Plan-and-Execute Terminal Assistant")
    parser.add_argument("--api-url", default="http://localhost:5000", help="Astro API URL")
    parser.add_argument("--api-key", help="API key (or set ASTRO_API_KEY env var)")
    parser.add_argument("-c", "--command", help="Execute single command and exit")
    args = parser.parse_args()
    
    cli = AstroCLI(api_url=args.api_url, api_key=args.api_key)
    
    if args.command:
        cli.chat(args.command)
    else:
        cli.run()


if __name__ == "__main__":
    main()
