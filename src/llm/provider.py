"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Dict, List, Optional, Any
import asyncio
import time


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "default"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Provider-specific options
    extra_headers: Optional[Dict[str, str]] = None
    extra_body: Optional[Dict[str, Any]] = None


@dataclass  
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    latency_ms: float = 0.0
    raw_response: Optional[Any] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.name = self.__class__.__name__.replace('Provider', '').lower()
    
    @abstractmethod
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Send completion request."""
        pass
    
    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream completion response."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available."""
        pass
    
    async def complete_with_retry(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> LLMResponse:
        """Complete with automatic retry logic."""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                start = time.time()
                response = await self.complete(messages, **kwargs)
                response.latency_ms = (time.time() - start) * 1000
                return response
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    await asyncio.sleep(delay)
        
        raise last_error
    
    def format_messages(self, system: Optional[str], user: str, history: Optional[List[Dict]] = None) -> List[Dict[str, str]]:
        """Format messages in provider-specific format."""
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": user})
        
        return messages
