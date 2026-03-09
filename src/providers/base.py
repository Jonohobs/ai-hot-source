"""Base provider interface and model registry."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelInfo:
    """Static metadata about a model."""
    name: str
    provider: str
    context_window: int
    cost_per_1k_in: float   # USD per 1k input tokens
    cost_per_1k_out: float  # USD per 1k output tokens
    supports_tools: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    tags: list[str] = field(default_factory=list)  # e.g. ["code", "reasoning", "fast", "local"]


@dataclass
class CompletionResult:
    """Standardised response from any provider."""
    content: str
    model: str
    provider: str
    tokens_in: int
    tokens_out: int
    latency_ms: float
    cost_usd: float
    raw: Any = None  # original API response for debugging


class Provider(ABC):
    """Abstract provider — one per API backend."""

    name: str

    @abstractmethod
    def models(self) -> list[ModelInfo]:
        """Return all models this provider offers."""
        ...

    @abstractmethod
    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> CompletionResult:
        """Send a chat completion request and return a standardised result."""
        ...

    def timed_complete(self, model: str, messages: list[dict[str, str]], **kwargs) -> CompletionResult:
        """Wrapper that measures latency."""
        start = time.perf_counter()
        result = self.complete(model, messages, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        result.latency_ms = elapsed
        return result
