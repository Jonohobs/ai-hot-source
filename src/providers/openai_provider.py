"""OpenAI / OpenAI-compatible provider (also covers OpenRouter, local vLLM, etc)."""

from __future__ import annotations

import os
import time
from typing import Any

from .base import CompletionResult, ModelInfo, Provider

# Lazy import — don't crash if openai isn't installed
_openai = None


def _get_openai():
    global _openai
    if _openai is None:
        import openai
        _openai = openai
    return _openai


# Default model catalogue — costs in USD per 1k tokens (approximate)
OPENAI_MODELS = [
    ModelInfo("gpt-4.1", "openai", 1_000_000, 0.002, 0.008, supports_tools=True, supports_vision=True, tags=["code", "reasoning"]),
    ModelInfo("gpt-4.1-mini", "openai", 1_000_000, 0.0004, 0.0016, supports_tools=True, supports_vision=True, tags=["fast", "code"]),
    ModelInfo("gpt-4.1-nano", "openai", 1_000_000, 0.0001, 0.0004, supports_tools=True, tags=["fast", "cheap"]),
    ModelInfo("o3", "openai", 200_000, 0.01, 0.04, supports_tools=True, tags=["reasoning"]),
    ModelInfo("o4-mini", "openai", 200_000, 0.0011, 0.0044, supports_tools=True, tags=["reasoning", "fast"]),
]


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        openai = _get_openai()
        self.client = openai.OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url,
        )

    def models(self) -> list[ModelInfo]:
        return OPENAI_MODELS

    def complete(self, model: str, messages: list[dict[str, str]],
                 temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> CompletionResult:
        start = time.perf_counter()
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        elapsed = (time.perf_counter() - start) * 1000
        choice = resp.choices[0]
        usage = resp.usage

        info = next((m for m in OPENAI_MODELS if m.name == model), None)
        cost = 0.0
        if info and usage:
            cost = (usage.prompt_tokens / 1000 * info.cost_per_1k_in +
                    usage.completion_tokens / 1000 * info.cost_per_1k_out)

        return CompletionResult(
            content=choice.message.content or "",
            model=model,
            provider=self.name,
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
            latency_ms=elapsed,
            cost_usd=cost,
            raw=resp,
        )
