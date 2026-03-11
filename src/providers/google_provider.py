"""Google Gemini provider."""

from __future__ import annotations

import os
import time

from .base import CompletionResult, ModelInfo, Provider

_google = None


def _get_google():
    global _google
    if _google is None:
        from google import genai
        _google = genai
    return _google


GOOGLE_MODELS = [
    ModelInfo("gemini-2.5-flash", "google", 1_000_000, 0.0, 0.0, supports_tools=True, supports_vision=True, tags=["fast", "free", "code"]),
    ModelInfo("gemini-2.5-pro", "google", 1_000_000, 0.00125, 0.01, supports_tools=True, supports_vision=True, tags=["reasoning", "code"]),
]


class GoogleProvider(Provider):
    name = "google"

    def __init__(self, api_key: str | None = None):
        genai = _get_google()
        self.client = genai.Client(api_key=api_key or os.environ.get("GOOGLE_API_KEY"))

    def models(self) -> list[ModelInfo]:
        return GOOGLE_MODELS

    def complete(self, model: str, messages: list[dict[str, str]],
                 temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> CompletionResult:
        genai = _get_google()

        # Convert chat format to Gemini contents
        contents = []
        system_instruction = None
        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            else:
                role = "user" if m["role"] == "user" else "model"
                contents.append(genai.types.Content(
                    role=role,
                    parts=[genai.types.Part(text=m["content"])],
                ))

        config = genai.types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        start = time.perf_counter()
        resp = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
        elapsed = (time.perf_counter() - start) * 1000

        content = resp.text or ""
        tokens_in = getattr(resp.usage_metadata, "prompt_token_count", 0) or 0
        tokens_out = getattr(resp.usage_metadata, "candidates_token_count", 0) or 0

        info = next((m for m in GOOGLE_MODELS if m.name == model), None)
        cost = 0.0
        if info:
            cost = (tokens_in / 1000 * info.cost_per_1k_in +
                    tokens_out / 1000 * info.cost_per_1k_out)

        return CompletionResult(
            content=content,
            model=model,
            provider=self.name,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=elapsed,
            cost_usd=cost,
            raw=resp,
        )
