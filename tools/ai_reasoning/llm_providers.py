"""
LLM Provider Integrations.

This module provides unified interfaces for OpenAI and Anthropic LLMs
with retry logic, error handling, and rate limiting.

Protocol Coverage:
- P-ORCHESTRATION: Multi-agent coordination
- P-RESOURCE: Resource allocation and optimization
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import asyncio
from abc import ABC, abstractmethod
import time


logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


@dataclass
class LLMResponse:
    """Unified LLM response format."""
    text: str
    token_count: int
    provider: str
    model: str
    finish_reason: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "token_count": self.token_count,
            "provider": self.provider,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata
        }


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(
        self,
        api_key: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_per_minute: int = 60
    ):
        """
        Initialize base provider.

        Args:
            api_key: API key for provider
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries (seconds)
            rate_limit_per_minute: Rate limit for requests
        """
        self.api_key = api_key
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_per_minute = rate_limit_per_minute

        self._request_times: List[float] = []
        self._total_tokens = 0

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """Generate completion from prompt."""
        pass

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        current_time = time.time()

        # Remove requests older than 1 minute
        self._request_times = [
            t for t in self._request_times if current_time - t < 60
        ]

        # Check if at limit
        if len(self._request_times) >= self.rate_limit_per_minute:
            sleep_time = 60 - (current_time - self._request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)

        self._request_times.append(current_time)

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise

                delay = self.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)

    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        return self._total_tokens


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        **kwargs
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4, gpt-3.5-turbo, etc.)
            **kwargs: Additional base provider arguments
        """
        super().__init__(api_key, **kwargs)
        self.model = model
        self._client = None

    async def _initialize_client(self):
        """Initialize OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI SDK not installed. Install with: pip install openai"
                )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using OpenAI API.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional API parameters

        Returns:
            LLMResponse
        """
        await self._initialize_client()
        await self._check_rate_limit()

        async def _make_request():
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            text = response.choices[0].message.content
            token_count = response.usage.total_tokens
            finish_reason = response.choices[0].finish_reason

            self._total_tokens += token_count

            return LLMResponse(
                text=text,
                token_count=token_count,
                provider="openai",
                model=self.model,
                finish_reason=finish_reason,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            )

        return await self._retry_with_backoff(_make_request)

    async def generate_streaming(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        Generate completion with streaming.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional API parameters

        Yields:
            Text chunks
        """
        await self._initialize_client()
        await self._check_rate_limit()

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(BaseLLMProvider):
    """Anthropic (Claude) LLM provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        **kwargs
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model to use (claude-3-opus, claude-3-sonnet, etc.)
            **kwargs: Additional base provider arguments
        """
        super().__init__(api_key, **kwargs)
        self.model = model
        self._client = None

    async def _initialize_client(self):
        """Initialize Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Anthropic SDK not installed. Install with: pip install anthropic"
                )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using Anthropic API.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional API parameters

        Returns:
            LLMResponse
        """
        await self._initialize_client()
        await self._check_rate_limit()

        async def _make_request():
            response = await self._client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            text = response.content[0].text
            token_count = response.usage.input_tokens + response.usage.output_tokens
            finish_reason = response.stop_reason

            self._total_tokens += token_count

            return LLMResponse(
                text=text,
                token_count=token_count,
                provider="anthropic",
                model=self.model,
                finish_reason=finish_reason,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            )

        return await self._retry_with_backoff(_make_request)

    async def generate_streaming(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        Generate completion with streaming.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional API parameters

        Yields:
            Text chunks
        """
        await self._initialize_client()
        await self._check_rate_limit()

        async with self._client.messages.stream(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        ) as stream:
            async for text in stream.text_stream:
                yield text


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        token_multiplier: float = 1.3,
        **kwargs
    ):
        """
        Initialize mock provider.

        Args:
            responses: List of pre-defined responses
            token_multiplier: Multiplier for token estimation
            **kwargs: Additional base provider arguments
        """
        super().__init__(api_key="mock_key", **kwargs)
        self.responses = responses or [
            "This is a mock response for testing purposes.",
            "Another mock response with different content.",
            "Final mock response to demonstrate functionality."
        ]
        self.token_multiplier = token_multiplier
        self.call_count = 0

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate mock completion.

        Args:
            prompt: Input prompt (used for token estimation)
            temperature: Ignored in mock
            max_tokens: Ignored in mock
            **kwargs: Ignored in mock

        Returns:
            LLMResponse with mock data
        """
        # Simulate some delay
        await asyncio.sleep(0.1)

        # Cycle through responses
        text = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1

        # Estimate tokens
        prompt_tokens = int(len(prompt.split()) * self.token_multiplier)
        completion_tokens = int(len(text.split()) * self.token_multiplier)
        token_count = prompt_tokens + completion_tokens

        self._total_tokens += token_count

        return LLMResponse(
            text=text,
            token_count=token_count,
            provider="mock",
            model="mock-model",
            finish_reason="stop",
            metadata={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "call_count": self.call_count
            }
        )


class LLMProviderFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create(
        provider_type: LLMProvider,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create LLM provider instance.

        Args:
            provider_type: Type of provider
            api_key: API key
            model: Model name (optional)
            **kwargs: Additional provider arguments

        Returns:
            LLM provider instance
        """
        if provider_type == LLMProvider.OPENAI:
            return OpenAIProvider(
                api_key=api_key,
                model=model or "gpt-4",
                **kwargs
            )
        elif provider_type == LLMProvider.ANTHROPIC:
            return AnthropicProvider(
                api_key=api_key,
                model=model or "claude-3-opus-20240229",
                **kwargs
            )
        elif provider_type == LLMProvider.MOCK:
            return MockLLMProvider(**kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider_type}")


class LLMProviderPool:
    """Pool of LLM providers for load balancing."""

    def __init__(self, providers: List[BaseLLMProvider]):
        """
        Initialize provider pool.

        Args:
            providers: List of LLM providers
        """
        self.providers = providers
        self.current_index = 0

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate using next available provider (round-robin).

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional API parameters

        Returns:
            LLMResponse
        """
        provider = self.providers[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.providers)

        return await provider.generate(prompt, temperature, max_tokens, **kwargs)

    def get_total_tokens(self) -> Dict[str, int]:
        """Get total tokens used by each provider."""
        return {
            f"provider_{i}": provider.get_total_tokens()
            for i, provider in enumerate(self.providers)
        }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        # Create mock provider for demonstration
        provider = LLMProviderFactory.create(
            provider_type=LLMProvider.MOCK,
            api_key="mock_key"
        )

        # Generate completion
        response = await provider.generate(
            prompt="What is the best architectural pattern for microservices?",
            temperature=0.7,
            max_tokens=500
        )

        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(f"Tokens: {response.token_count}")
        print(f"Response: {response.text}")
        print(f"Total tokens used: {provider.get_total_tokens()}")

    asyncio.run(main())
