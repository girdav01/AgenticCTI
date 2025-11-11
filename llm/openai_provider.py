"""
OpenAI LLM provider.
"""

from typing import List, Optional
import logging
from .base import BaseLLM, LLMMessage, LLMResponse, LLMAPIError, LLMRateLimitError

try:
    from openai import OpenAI, APIError, RateLimitError, APIConnectionError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class OpenAILLM(BaseLLM):
    """OpenAI LLM provider."""

    def __init__(
        self,
        model: str,
        api_key: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs
    ):
        """
        Initialize OpenAI provider.

        Args:
            model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
            api_key: OpenAI API key
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Raises:
            ImportError: If openai package not installed
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is required. Install with: pip install openai")

        super().__init__(model, temperature, max_tokens, **kwargs)
        self.client = OpenAI(api_key=api_key)
        logger.info(f"Initialized OpenAI provider with model: {model}")

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
            LLMAPIError: If API call fails
            LLMRateLimitError: If rate limit exceeded
        """
        try:
            # Convert messages to OpenAI format
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )

            choice = response.choices[0]

            return LLMResponse(
                content=choice.message.content,
                model=response.model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=choice.finish_reason,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                }
            )

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise LLMRateLimitError(f"Rate limit exceeded: {e}")
        except APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            raise LLMAPIError(f"Connection error: {e}")
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMAPIError(f"API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI generate: {e}")
            raise LLMAPIError(f"Unexpected error: {e}")

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
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt)
        ]
        return self.generate(messages, **kwargs)
