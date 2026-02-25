"""OpenAI provider implementation."""

import os
from typing import AsyncIterator, Dict, List, Optional

try:
    from openai import AsyncOpenAI, OpenAIError
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAIError = Exception

from .provider import LLMProvider, LLMResponse, LLMConfig


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    DEFAULT_MODEL = "gpt-4o-mini"
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)
            )
        super().__init__(config)
        
        if not HAS_OPENAI:
            raise ImportError("openai package required. Run: pip install openai")
        
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )
    
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Send completion request to OpenAI."""
        model = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers=self.config.extra_headers,
                **{k: v for k, v in (self.config.extra_body or {}).items() if v is not None}
            )
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                provider="openai",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                finish_reason=response.choices[0].finish_reason,
                raw_response=response
            )
        except OpenAIError as e:
            raise RuntimeError(f"OpenAI API error: {e}")
    
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream completion from OpenAI."""
        model = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
