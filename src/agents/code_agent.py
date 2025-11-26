"""
Code Agent with Real Generation and Execution Capabilities

REFACTORED: Full async implementation.
- Async subprocess execution (asyncio.create_subprocess_exec)
- Async LLM API calls (AsyncOpenAI)
- Optional Docker sandbox for secure code execution
- Improved security validation with regex patterns
"""
import asyncio
import logging
import os
import tempfile
import re
import shutil
import sys
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent, AgentCapability, AgentContext, TaskResult, AgentState
from core.llm_factory import LLMFactory

# Try to import openai with async support
try:
    from openai import OpenAI, AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None
    AsyncOpenAI = None

# Check if Docker is available for sandboxed execution
HAS_DOCKER = shutil.which('docker') is not None

logger = logging.getLogger("CodeAgent")

class CodeAgent(BaseAgent):
    def __init__(self, agent_id: str, config: Dict[str, Any], llm_client: Any = None):
        super().__init__(agent_id, [AgentCapability.OPTIMIZATION], config)
        
        self.safe_mode = config.get("safe_mode", True)
        self.use_docker = config.get("use_docker_sandbox", False) and HAS_DOCKER
        self.docker_image = config.get("docker_image", "python:3.11-slim")
        self.provider = config.get("llm_provider", "openai").lower()
        self.model_name = config.get("model_name", "gpt-3.5-turbo")
        
        # Configurable timeouts
        self.local_timeout = config.get("local_execution_timeout", 10.0)
        self.docker_timeout = config.get("docker_execution_timeout", 30.0)
        
        # LLM clients
        self.async_client: Optional[AsyncOpenAI] = None
        self.sync_client: Optional[OpenAI] = None  # Fallback
        
        # Use injected client if provided, otherwise initialize
        if llm_client:
            if HAS_OPENAI and isinstance(llm_client, AsyncOpenAI):
                self.async_client = llm_client
            elif HAS_OPENAI and isinstance(llm_client, OpenAI):
                self.sync_client = llm_client
            else:
                # Try to detect type if imports failed or check type name
                if "AsyncOpenAI" in str(type(llm_client)):
                     self.async_client = llm_client
                else:
                     self.sync_client = llm_client
        else:
            self._initialize_clients(config)
        
        if self.use_docker:
            logger.info(f"Docker sandbox enabled with image: {self.docker_image}")
            # Validate docker image exists (async check would be better but __init__ is sync)
            self._docker_image_validated = False
        elif config.get("use_docker_sandbox", False):
            logger.warning("Docker sandbox requested but Docker is not available")

    def _initialize_clients(self, config: Dict[str, Any]):
        """Initialize LLM clients using Factory"""
        api_key = config.get("api_key")
        base_url = config.get("api_base")
        
        # Create Async Client (Primary)
        self.async_client = LLMFactory.create_client(
            provider=self.provider,
            api_key=api_key,
            base_url=base_url
        )
        
        # Create Sync Client (Fallback)
        self.sync_client = LLMFactory.create_sync_client(
            provider=self.provider,
            api_key=api_key,
            base_url=base_url
        )
        
        if self.async_client:
            logger.info(f"Initialized CodeAgent with async client for provider: {self.provider}")
        elif self.sync_client:
            logger.info(f"Initialized CodeAgent with sync client for provider: {self.provider}")
        else:
            logger.warning(f"Failed to initialize any LLM client for {self.provider}")

    async def execute_task(self, task: Dict[str, Any], context: AgentContext) -> TaskResult:
        try:
            self.state = AgentState.BUSY
            task_type = task.get('payload', {}).get('code_task_type', 'generate_code')
            requirements = task.get('payload', {}).get('requirements', '')
            
            if task_type == 'generate_code':
                return await self._generate_code(requirements)
            elif task_type == 'execute_code':
                code = task.get('payload', {}).get('code')
                return await self._execute_code(code)
            else:
                return TaskResult(success=False, error_message=f"Unknown task type: {task_type}")

        except Exception as e:
            logger.error(f"Code task failed: {e}")
            return TaskResult(success=False, error_message=str(e))
        finally:
            self.state = AgentState.ACTIVE

    async def _generate_code(self, requirements: str) -> TaskResult:
        """Generate code using async LLM API (non-blocking)"""
        if not self.async_client and not self.sync_client:
            return TaskResult(success=False, error_message=f"LLM client not initialized for {self.provider}. Cannot generate code.")

        try:
            logger.info(f"Generating code using {self.provider} ({self.model_name})...")
            
            messages = [
                {"role": "system", "content": "You are a Python code generator. Output ONLY valid Python code. No markdown backticks. Do not include any explanations."},
                {"role": "user", "content": requirements}
            ]
            
            # Use async client if available (non-blocking)
            if self.async_client:
                response = await self.async_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages
                )
            else:
                # Fallback to sync client in thread
                response = await asyncio.to_thread(
                    self.sync_client.chat.completions.create,
                    model=self.model_name,
                    messages=messages
                )
            
            code = response.choices[0].message.content
            
            # Clean up code if it contains markdown
            code = self._clean_code_response(code)
                
            return TaskResult(success=True, result_data={'code': code})
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            return TaskResult(success=False, error_message=f"LLM Generation failed: {e}")
    
    def _clean_code_response(self, code: Optional[str]) -> str:
        """Clean up LLM response to extract pure code"""
        if not code:
            return ""
        
        code = code.strip()
        
        # Remove markdown code blocks
        if code.startswith("```"):
            # Find the end of the first line (language identifier)
            first_newline = code.find("\n")
            if first_newline != -1:
                code = code[first_newline + 1:]
        
        if code.endswith("```"):
            code = code[:-3].rstrip()
        
        # Remove language identifier if still present
        if code.startswith("python"):
            code = code[6:].lstrip()
        
        return code

    async def _execute_code(self, code: str) -> TaskResult:
        """Execute Python code - uses Docker sandbox if enabled, otherwise async subprocess"""
        if not code:
            return TaskResult(success=False, error_message="No code provided for execution")
        
        # Use Docker sandbox if enabled (more secure)
        if self.use_docker:
            return await self._execute_code_docker(code)
        
        # Otherwise use local subprocess with security checks
        # Enhanced Security Check (still naive - production should use Docker/Wasm sandboxing)
        security_result = self._security_check(code)
        if security_result:
            return security_result

        return await self._execute_code_local(code)
    
    async def _execute_code_local(self, code: str) -> TaskResult:
        """Execute code locally using async subprocess"""
        temp_path = None
        try:
            # Write to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name

            # Get Python executable path for consistency
            python_executable = sys.executable or 'python'
            
            # NON-BLOCKING EXECUTION using asyncio subprocess
            proc = await asyncio.create_subprocess_exec(
                python_executable, temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                # Wait for completion with timeout (non-blocking)
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.local_timeout
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                proc.kill()
                await proc.wait()  # Clean up zombie process
                return TaskResult(success=False, error_message=f"Code execution timed out ({self.local_timeout}s limit)")

            if proc.returncode == 0:
                return TaskResult(success=True, result_data={'output': stdout.decode('utf-8', errors='replace')})
            else:
                return TaskResult(success=False, error_message=f"Execution Error: {stderr.decode('utf-8', errors='replace')}")

        except Exception as e:
            return TaskResult(success=False, error_message=f"Execution failed: {e}")
        finally:
            # Cleanup temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass  # Best effort cleanup
    
    async def _execute_code_docker(self, code: str) -> TaskResult:
        """
        Execute code in an ephemeral Docker container for security isolation.
        
        Container features:
        - No network access (--network none)
        - Read-only filesystem (--read-only)
        - Limited memory (--memory 128m)
        - Limited CPU (--cpus 0.5)
        - Dropped capabilities (--cap-drop ALL)
        - Auto-removed after execution (--rm)
        """
        temp_path = None
        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Make temp file readable (skip on Windows where chmod behaves differently)
            if sys.platform != 'win32':
                os.chmod(temp_path, 0o644)
            
            # Docker command with security constraints
            docker_cmd = [
                'docker', 'run',
                '--rm',                          # Auto-remove container
                '--network', 'none',             # No network access
                '--read-only',                   # Read-only filesystem
                '--memory', '128m',              # Memory limit
                '--cpus', '0.5',                 # CPU limit
                '--cap-drop', 'ALL',             # Drop all capabilities
                '--security-opt', 'no-new-privileges',
                '-v', f'{temp_path}:/code/script.py:ro',  # Mount code read-only
                '-w', '/code',                   # Working directory
                self.docker_image,
                'python', '/code/script.py'
            ]
            
            logger.info(f"Executing code in Docker sandbox ({self.docker_image})")
            
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.docker_timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return TaskResult(success=False, error_message=f"Docker execution timed out ({self.docker_timeout}s limit)")
            
            if proc.returncode == 0:
                return TaskResult(
                    success=True, 
                    result_data={
                        'output': stdout.decode('utf-8', errors='replace'),
                        'execution_environment': 'docker',
                        'docker_image': self.docker_image
                    }
                )
            else:
                return TaskResult(
                    success=False, 
                    error_message=f"Docker Execution Error: {stderr.decode('utf-8', errors='replace')}"
                )
                
        except FileNotFoundError:
            return TaskResult(success=False, error_message="Docker not found. Please install Docker or disable sandbox mode.")
        except Exception as e:
            return TaskResult(success=False, error_message=f"Docker execution failed: {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
    
    def _security_check(self, code: str) -> Optional[TaskResult]:
        """
        Perform security validation on code.
        
        WARNING: This is still naive string matching. Production systems should:
        - Execute in ephemeral Docker containers
        - Use WebAssembly (Wasm) sandboxes
        - Implement proper AST-based analysis
        """
        if not self.safe_mode:
            return None
            
        # Patterns that could bypass simple string matching
        # This is improved but still not production-safe
        forbidden_patterns = [
            r'\bimport\s+os\b',
            r'\bimport\s+sys\b',
            r'\bimport\s+subprocess\b',
            r'\bfrom\s+os\s+import\b',
            r'\bfrom\s+sys\s+import\b',
            r'\bfrom\s+subprocess\s+import\b',
            r'__import__\s*\(\s*["\']os["\']',
            r'__import__\s*\(\s*["\']sys["\']',
            r'__import__\s*\(\s*["\']subprocess["\']',
            r'\bexec\s*\(',
            r'\beval\s*\(',
            r'\bopen\s*\([^)]*["\'][wax]',  # Write mode file operations
            r'\bcompile\s*\(',
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return TaskResult(
                    success=False, 
                    error_message=f"Security Alert: Code contains forbidden pattern. Execution blocked in Safe Mode. Consider using a sandboxed environment for untrusted code."
                )
        
        return None