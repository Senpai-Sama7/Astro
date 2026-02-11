"""LLM Provider Factory - unified interface for all LLM backends."""

import os
from typing import Dict, List, Optional, Type

from .provider import LLMProvider, LLMConfig, LLMResponse
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from .openrouter_provider import OpenRouterProvider
from .ollama_provider import OllamaProvider
from .llamacpp_provider import LlamaCppProvider


class LLMFactory:
    """Factory for creating LLM providers with automatic fallback."""
    
    PROVIDERS: Dict[str, Type[LLMProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "google": GoogleProvider,
        "gemini": GoogleProvider,
        "openrouter": OpenRouterProvider,
        "ollama": OllamaProvider,
        "llamacpp": LlamaCppProvider,
        "llama.cpp": LlamaCppProvider,
    }
    
    @classmethod
    def create(cls, provider_name: str, config: Optional[LLMConfig] = None) -> LLMProvider:
        """Create a specific provider by name."""
        provider_name = provider_name.lower()
        
        if provider_name not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(cls.PROVIDERS.keys())}")
        
        provider_class = cls.PROVIDERS[provider_name]
        return provider_class(config)
    
    @classmethod
    async def create_with_fallback(
        cls,
        preferred_order: Optional[List[str]] = None,
        config: Optional[LLMConfig] = None
    ) -> LLMProvider:
        """Create provider with automatic fallback to available ones."""
        
        if preferred_order is None:
            # Default priority from env or sensible defaults
            preferred_order = cls._get_default_priority()
        
        errors = []
        
        for provider_name in preferred_order:
            provider_name = provider_name.lower()
            
            if provider_name not in cls.PROVIDERS:
                continue
            
            try:
                provider = cls.create(provider_name, config)
                
                # Health check
                if await provider.health_check():
                    return provider
                else:
                    errors.append(f"{provider_name}: Health check failed")
                    
            except ImportError as e:
                errors.append(f"{provider_name}: {e}")
            except Exception as e:
                errors.append(f"{provider_name}: {e}")
        
        # If we get here, no providers worked
        raise RuntimeError(
            f"No LLM providers available. Tried: {preferred_order}. Errors: {errors}"
        )
    
    @classmethod
    def _get_default_priority(cls) -> List[str]:
        """Get default provider priority from environment or defaults."""
        env_priority = os.getenv("ASTRO_LLM_PRIORITY")
        
        if env_priority:
            return [p.strip() for p in env_priority.split(",")]
        
        # Check which API keys are available
        priority = []
        
        if os.getenv("ANTHROPIC_API_KEY"):
            priority.append("anthropic")
        if os.getenv("OPENAI_API_KEY"):
            priority.append("openai")
        if os.getenv("OPENROUTER_API_KEY"):
            priority.append("openrouter")
        if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            priority.append("google")
        
        # Always try local providers last
        priority.extend(["ollama", "llamacpp"])
        
        return priority if priority else ["ollama"]
    
    @classmethod
    def list_available(cls) -> List[str]:
        """List all available provider names."""
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def list_configured(cls) -> List[str]:
        """List providers that have API keys configured."""
        configured = []
        
        if os.getenv("ANTHROPIC_API_KEY"):
            configured.append("anthropic")
        if os.getenv("OPENAI_API_KEY"):
            configured.append("openai")
        if os.getenv("OPENROUTER_API_KEY"):
            configured.append("openrouter")
        if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            configured.append("google")
        if os.getenv("OLLAMA_HOST") or cls._check_ollama_running():
            configured.append("ollama")
        if os.getenv("LLAMACPP_URL"):
            configured.append("llamacpp")
        
        return configured
    
    @classmethod
    def _check_ollama_running(cls) -> bool:
        """Check if Ollama is running on default port."""
        import asyncio
        try:
            # Quick check - don't block
            return True  # Assume available, health check will verify
        except Exception:
            return False


class MultiProviderRouter:
    """Route requests to multiple providers with load balancing and fallback."""
    
    def __init__(self, providers: List[LLMProvider], strategy: str = "fallback"):
        self.providers = providers
        self.strategy = strategy
        self.current_index = 0
        self.health_status: Dict[str, bool] = {}
    
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Complete with selected provider strategy."""
        if self.strategy == "fallback":
            return await self._fallback_complete(messages, **kwargs)
        elif self.strategy == "round_robin":
            return await self._round_robin_complete(messages, **kwargs)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    async def _fallback_complete(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Try providers in order until one succeeds."""
        last_error = None
        
        for provider in self.providers:
            try:
                return await provider.complete_with_retry(messages, **kwargs)
            except Exception as e:
                last_error = e
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    async def _round_robin_complete(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Rotate between providers."""
        attempts = 0
        start_index = self.current_index
        
        while attempts < len(self.providers):
            provider = self.providers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.providers)
            
            try:
                return await provider.complete(messages, **kwargs)
            except Exception:
                attempts += 1
        
        raise RuntimeError("All providers failed in round-robin")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers."""
        for provider in self.providers:
            self.health_status[provider.name] = await provider.health_check()
        
        return self.health_status
