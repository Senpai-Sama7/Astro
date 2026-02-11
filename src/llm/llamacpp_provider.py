"""llama.cpp provider for local model inference (server mode)."""

import os
import aiohttp
from typing import AsyncIterator, Dict, List, Optional, Any

from .provider import LLMProvider, LLMResponse, LLMConfig


class LlamaCppProvider(LLMProvider):
    """llama.cpp server - high-performance local inference.
    
    Requires llama.cpp server running.
    GitHub: https://github.com/ggerganov/llama.cpp
    
    Start server: ./server -m model.gguf --port 8080
    """
    
    DEFAULT_URL = "http://localhost:8080"
    DEFAULT_MODEL = "local-model"
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                base_url=os.getenv("LLAMACPP_URL", self.DEFAULT_URL),
                model=os.getenv("LLAMACPP_MODEL", self.DEFAULT_MODEL)
            )
        super().__init__(config)
        
        self.base_url = config.base_url or self.DEFAULT_URL
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI format to simple prompt format."""
        formatted = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                formatted.append(f"<|system|>\n{content}")
            elif role == "user":
                formatted.append(f"<|user|>\n{content}")
            elif role == "assistant":
                formatted.append(f"<|assistant|>\n{content}")
        
        formatted.append("<|assistant|>\n")
        return "\n".join(formatted)
    
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Send completion request to llama.cpp server."""
        model = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        prompt = self._convert_messages(messages)
        
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            payload["n_predict"] = max_tokens
        
        # Add any extra options
        if self.config.extra_body:
            payload.update(self.config.extra_body)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"llama.cpp error {response.status}: {error_text}")
                
                data = await response.json()
                
                return LLMResponse(
                    content=data.get("content", ""),
                    model=model,
                    provider="llamacpp",
                    usage={
                        "prompt_tokens": data.get("tokens_evaluated", 0),
                        "completion_tokens": data.get("tokens_predicted", 0),
                        "total_tokens": data.get("tokens_evaluated", 0) + data.get("tokens_predicted", 0)
                    },
                    finish_reason="stop" if data.get("stop") else None,
                    raw_response=data
                )
    
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream completion from llama.cpp server."""
        model = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        prompt = self._convert_messages(messages)
        
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["n_predict"] = max_tokens
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                async for line in response.content:
                    try:
                        import json
                        data = json.loads(line)
                        if "content" in data:
                            yield data["content"]
                    except json.JSONDecodeError:
                        continue
    
    async def health_check(self) -> bool:
        """Check if llama.cpp server is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/props") as response:
                return await response.json()
    
    async def tokenize(self, text: str) -> List[int]:
        """Tokenize text using the model's tokenizer."""
        payload = {"content": text}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/tokenize", json=payload) as response:
                data = await response.json()
                return data.get("tokens", [])
