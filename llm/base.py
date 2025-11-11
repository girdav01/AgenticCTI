"""
Base LLM interface for AgenticCTI.
Provides abstraction for different LLM providers (Ollama, OpenAI, Anthropic).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    """Represents a message in LLM conversation."""
    role: str  # 'system', 'user', 'assistant'
    content: str


@dataclass
class LLMResponse:
    """Represents an LLM response."""
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs
    ):
        """
        Initialize LLM provider.

        Args:
            model: Model identifier
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs

        logger.info(f"Initialized {self.__class__.__name__} with model: {model}")

    @abstractmethod
    def generate(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion from messages.

        Args:
            messages: List of conversation messages
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse object

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion with system and user prompts.

        Args:
            system_prompt: System instruction
            user_prompt: User query
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse object
        """
        pass

    def validate_response(self, response: LLMResponse) -> bool:
        """
        Validate LLM response.

        Args:
            response: Response to validate

        Returns:
            True if valid, False otherwise
        """
        if not response or not response.content:
            logger.warning("Empty or invalid LLM response")
            return False

        if len(response.content.strip()) < 10:
            logger.warning("LLM response too short")
            return False

        return True


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """Exception for connection errors."""
    pass


class LLMAPIError(LLMError):
    """Exception for API errors."""
    pass


class LLMRateLimitError(LLMError):
    """Exception for rate limit errors."""
    pass
