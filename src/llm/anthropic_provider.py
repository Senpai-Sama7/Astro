"""Anthropic Claude provider implementation."""

import os
from typing import AsyncIterator, Dict, List, Optional

try:
    from anthropic import AsyncAnthropic, AnthropicError
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    AnthropicError = Exception

from .provider import LLMProvider, LLMResponse, LLMConfig


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.getenv("ANTHROPIC_MODEL", self.DEFAULT_MODEL)
            )
        super().__init__(config)
        
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package required. Run: pip install anthropic")
        
        self.client = AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )
    
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Send completion request to Anthropic."""
        model = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens or 4096)
        
        # Extract system message if present
        system = None
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)
        
        try:
            response = await self.client.messages.create(
                model=model,
                messages=chat_messages,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = "".join(block.text for block in response.content if block.type == "text")
            
            return LLMResponse(
                content=content,
                model=response.model,
                provider="anthropic",
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                finish_reason=response.stop_reason,
                raw_response=response
            )
        except AnthropicError as e:
            raise RuntimeError(f"Anthropic API error: {e}")
    
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream completion from Anthropic."""
        model = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens or 4096)
        
        system = None
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)
        
        async with self.client.messages.stream(
            model=model,
            messages=chat_messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        ) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible."""
        try:
            # Try a minimal request
            await self.client.messages.create(
                model=self.DEFAULT_MODEL,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
