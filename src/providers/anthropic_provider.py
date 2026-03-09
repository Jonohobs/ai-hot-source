"""Anthropic provider."""

from __future__ import annotations

import os
import time
from typing import Any

from .base import CompletionResult, ModelInfo, Provider

_anthropic = None


def _get_anthropic():
    global _anthropic
    if _anthropic is None:
        import anthropic
        _anthropic = anthropic
    return _anthropic


ANTHROPIC_MODELS = [
    ModelInfo("claude-opus-4-6", "anthropic", 200_000, 0.015, 0.075, supports_tools=True, supports_vision=True, tags=["reasoning", "code"]),
    ModelInfo("claude-sonnet-4-6", "anthropic", 200_000, 0.003, 0.015, supports_tools=True, supports_vision=True, tags=["code", "fast"]),
    ModelInfo("claude-haiku-4-5-20251001", "anthropic", 200_000, 0.0008, 0.004, supports_tools=True, tags=["fast", "cheap"]),
]


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None):
        anthropic = _get_anthropic()
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
        )

    def models(self) -> list[ModelInfo]:
        return ANTHROPIC_MODELS

    def complete(self, model: str, messages: list[dict[str, str]],
                 temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> CompletionResult:
        # Anthropic separates system from messages
        system_msg = ""
        chat_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg += m["content"] + "\n"
            else:
                chat_msgs.append(m)

        start = time.perf_counter()
        resp = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_msg.strip() if system_msg else None,
            messages=chat_msgs,
            **kwargs,
        )
        elapsed = (time.perf_counter() - start) * 1000

        content = ""
        for block in resp.content:
            if hasattr(block, "text"):
                content += block.text

        info = next((m for m in ANTHROPIC_MODELS if m.name == model), None)
        cost = 0.0
        if info and resp.usage:
            cost = (resp.usage.input_tokens / 1000 * info.cost_per_1k_in +
                    resp.usage.output_tokens / 1000 * info.cost_per_1k_out)

        return CompletionResult(
            content=content,
            model=model,
            provider=self.name,
            tokens_in=resp.usage.input_tokens if resp.usage else 0,
            tokens_out=resp.usage.output_tokens if resp.usage else 0,
            latency_ms=elapsed,
            cost_usd=cost,
            raw=resp,
        )
