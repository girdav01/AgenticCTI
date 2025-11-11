"""
LLM Factory for creating appropriate LLM provider instances.
"""

import os
import logging
from typing import Optional
from .base import BaseLLM
from .ollama_provider import OllamaLLM
from .openai_provider import OpenAILLM

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create_llm(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLM:
        """
        Create an LLM provider instance.

        Args:
            provider: Provider name ('ollama', 'openai', 'anthropic')
            model: Model identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            BaseLLM instance

        Raises:
            ValueError: If provider is not supported or configuration is invalid
        """
        # Get provider from env if not specified
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "ollama").lower()

        # Get model from env if not specified
        if model is None:
            model = os.getenv("LLM_MODEL", "llama3.2:latest")

        logger.info(f"Creating LLM provider: {provider} with model: {model}")

        # Get common parameters from env
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

        try:
            if provider == "ollama":
                base_url = kwargs.get("base_url") or os.getenv("LLM_BASE_URL", "http://localhost:11434")
                return OllamaLLM(
                    model=model,
                    base_url=base_url,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

            elif provider == "openai":
                api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

                return OpenAILLM(
                    model=model,
                    api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

            elif provider == "anthropic":
                # Anthropic provider can be implemented similarly
                raise NotImplementedError("Anthropic provider not yet implemented")

            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to create LLM provider {provider}: {e}")
            raise

    @staticmethod
    def get_default_llm(**kwargs) -> BaseLLM:
        """
        Get default LLM instance based on environment configuration.

        Args:
            **kwargs: Additional parameters to override defaults

        Returns:
            BaseLLM instance
        """
        return LLMFactory.create_llm(**kwargs)
