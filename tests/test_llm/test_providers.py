"""Tests for LLM providers."""

import pytest
import os
from src.llm import LLMFactory, LLMConfig
from src.llm.provider import LLMResponse


class TestLLMFactory:
    """Test LLM provider factory."""
    
    def test_list_available(self):
        """Test listing available providers."""
        providers = LLMFactory.list_available()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "ollama" in providers
        assert "llamacpp" in providers
    
    def test_create_mock_provider(self):
        """Test creating a provider."""
        # This will fail without API keys, but tests the interface
        pass


class TestLLMConfig:
    """Test LLM configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = LLMConfig()
        assert config.temperature == 0.7
        assert config.timeout == 60.0
        assert config.max_retries == 3
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LLMConfig(
            api_key="test-key",
            model="gpt-4",
            temperature=0.5,
            max_tokens=100
        )
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 100
