"""Ollama provider for local model inference."""

import os
import aiohttp
from typing import AsyncIterator, Dict, List, Optional, Any

from .provider import LLMProvider, LLMResponse, LLMConfig


class OllamaProvider(LLMProvider):
    """Ollama - run LLMs locally.
    
    Requires Ollama server running locally or remotely.
    Install: https://ollama.com
    """
    
    DEFAULT_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2"
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                base_url=os.getenv("OLLAMA_HOST", self.DEFAULT_URL),
                model=os.getenv("OLLAMA_MODEL", self.DEFAULT_MODEL)
            )
        super().__init__(config)
        
        self.base_url = config.base_url or self.DEFAULT_URL
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert OpenAI format to Ollama format."""
        system = None
        prompt_parts = []
        
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            elif msg["role"] == "user":
                prompt_parts.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                prompt_parts.append(f"Assistant: {msg['content']}")
        
        prompt = "\n".join(prompt_parts) + "\nAssistant:"
        return system, prompt
    
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Send completion request to Ollama."""
        model = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        
        system, prompt = self._convert_messages(messages)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        if self.config.max_tokens:
            payload["options"]["num_predict"] = self.config.max_tokens
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Ollama error {response.status}: {error_text}")
                
                data = await response.json()
                
                return LLMResponse(
                    content=data.get("response", ""),
                    model=model,
                    provider="ollama",
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    },
                    finish_reason="stop" if not data.get("done_reason") else data.get("done_reason"),
                    raw_response=data
                )
    
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream completion from Ollama."""
        model = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        
        system, prompt = self._convert_messages(messages)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                async for line in response.content:
                    try:
                        import json
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue
    
    async def health_check(self) -> bool:
        """Check if Ollama server is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models in Ollama."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/tags") as response:
                data = await response.json()
                return data.get("models", [])
    
    async def pull_model(self, model: str) -> Dict[str, Any]:
        """Pull a model from Ollama hub."""
        payload = {"name": model}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/pull", json=payload) as response:
                return await response.json()
