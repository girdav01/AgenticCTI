"""
LLM Handler for multiple providers
Supports: Ollama, LM Studio, OpenAI, Anthropic, Azure
"""

import requests
import json
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion"""
        pass

class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Ollama"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', 0.7),
                "num_predict": kwargs.get('max_tokens', 2000)
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            raise Exception(f"Ollama generation error: {str(e)}")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using Ollama"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', 0.7),
                "num_predict": kwargs.get('max_tokens', 2000)
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()['message']['content']
        except Exception as e:
            raise Exception(f"Ollama chat error: {str(e)}")

class LMStudioProvider(BaseLLMProvider):
    """LM Studio local LLM provider (OpenAI-compatible API)"""
    
    def __init__(self, base_url: str, model: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key or "not-needed"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using LM Studio"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using LM Studio"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 2000)
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"LM Studio error: {str(e)}")

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""
    
    def __init__(self, model: str, api_key: str, base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using OpenAI"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 2000)
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"OpenAI error: {str(e)}")

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Claude"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using Claude"""
        url = f"{self.base_url}/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', 2000),
            "temperature": kwargs.get('temperature', 0.7)
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()['content'][0]['text']
        except Exception as e:
            raise Exception(f"Anthropic error: {str(e)}")

class LLMHandler:
    """Main LLM handler that manages different providers"""
    
    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama3.2",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.provider_name = provider.lower()
        self.model = model
        
        # Initialize appropriate provider
        if self.provider_name == "ollama":
            self.provider = OllamaProvider(
                base_url=base_url or "http://localhost:11434",
                model=model
            )
        elif self.provider_name == "lmstudio":
            self.provider = LMStudioProvider(
                base_url=base_url or "http://localhost:1234/v1",
                model=model,
                api_key=api_key
            )
        elif self.provider_name == "openai":
            if not api_key:
                raise ValueError("API key required for OpenAI")
            self.provider = OpenAIProvider(
                model=model,
                api_key=api_key,
                base_url=base_url
            )
        elif self.provider_name == "anthropic":
            if not api_key:
                raise ValueError("API key required for Anthropic")
            self.provider = AnthropicProvider(
                model=model,
                api_key=api_key
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        return self.provider.generate(prompt, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion"""
        return self.provider.chat(messages, **kwargs)
    
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        try:
            test_response = self.generate("test", max_tokens=10)
            return True
        except:
            return False
