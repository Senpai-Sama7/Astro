"""Google Gemini provider implementation."""

import os
import asyncio
from typing import AsyncIterator, Dict, List, Optional

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

from .provider import LLMProvider, LLMResponse, LLMConfig


class GoogleProvider(LLMProvider):
    """Google Gemini provider."""
    
    DEFAULT_MODEL = "gemini-1.5-flash"
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
                model=os.getenv("GOOGLE_MODEL", self.DEFAULT_MODEL)
            )
        super().__init__(config)
        
        if not HAS_GOOGLE:
            raise ImportError("google-generativeai package required. Run: pip install google-generativeai")
        
        genai.configure(api_key=config.api_key)
        self.genai = genai
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert OpenAI format to Gemini format."""
        system = None
        chat_history = []
        
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            elif msg["role"] == "user":
                chat_history.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                chat_history.append({"role": "model", "parts": [msg["content"]]})
        
        return system, chat_history
    
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Send completion request to Google Gemini."""
        model_name = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        system, chat_history = self._convert_messages(messages)
        
        try:
            model = self.genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system
            )
            
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            # Get last user message
            if chat_history:
                last_message = chat_history[-1]["parts"][0]
                response = await asyncio.wait_for(
                    model.generate_content_async(
                        last_message,
                        generation_config=generation_config
                    ),
                    timeout=self.config.timeout
                )
            else:
                response = await asyncio.wait_for(
                    model.generate_content_async(
                        "Hello",
                        generation_config=generation_config
                    ),
                    timeout=self.config.timeout
                )
            
            return LLMResponse(
                content=response.text,
                model=model_name,
                provider="google",
                usage=None,  # Gemini doesn't always provide token counts
                finish_reason="stop" if response.candidates else None,
                raw_response=response
            )
        except Exception as e:
            raise RuntimeError(f"Google API error: {e}")
    
    async def stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream completion from Google Gemini."""
        model_name = kwargs.get('model', self.config.model)
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        system, chat_history = self._convert_messages(messages)
        
        model = self.genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system
        )
        
        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        if chat_history:
            last_message = chat_history[-1]["parts"][0]
            response = await model.generate_content_async(
                last_message,
                generation_config=generation_config,
                stream=True
            )
        else:
            response = await model.generate_content_async(
                "Hello",
                generation_config=generation_config,
                stream=True
            )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text
    
    async def health_check(self) -> bool:
        """Check if Google API is accessible."""
        try:
            model = self.genai.GenerativeModel(self.DEFAULT_MODEL)
            _response = await model.generate_content_async("test", generation_config=GenerationConfig(max_output_tokens=1))
            return True
        except Exception:
            return False
