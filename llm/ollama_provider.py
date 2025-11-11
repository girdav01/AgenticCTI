"""
Ollama LLM provider for local model inference.
"""

from typing import List, Optional
import requests
import logging
from .base import BaseLLM, LLMMessage, LLMResponse, LLMConnectionError, LLMAPIError

logger = logging.getLogger(__name__)


class OllamaLLM(BaseLLM):
    """Ollama LLM provider for local models."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 120,
        **kwargs
    ):
        """
        Initialize Ollama provider.

        Args:
            model: Model name (e.g., 'llama3.2:latest')
            base_url: Ollama server URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            **kwargs: Additional parameters
        """
        super().__init__(model, temperature, max_tokens, **kwargs)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Verify connection to Ollama server."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Successfully connected to Ollama at {self.base_url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise LLMConnectionError(f"Cannot connect to Ollama at {self.base_url}: {e}")

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
        """
        try:
            # Convert messages to Ollama format
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.temperature),
                    "num_predict": kwargs.get("max_tokens", self.max_tokens),
                }
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=self.model,
                tokens_used=data.get("eval_count"),
                finish_reason=data.get("done_reason"),
                metadata={
                    "total_duration": data.get("total_duration"),
                    "load_duration": data.get("load_duration"),
                    "prompt_eval_count": data.get("prompt_eval_count"),
                }
            )

        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            raise LLMAPIError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise LLMAPIError(f"Ollama API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Ollama generate: {e}")
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

    def pull_model(self) -> bool:
        """
        Pull/download the model if not available.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Pulling model {self.model}...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=600  # 10 minutes for model download
            )
            response.raise_for_status()
            logger.info(f"Successfully pulled model {self.model}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {self.model}: {e}")
            return False
