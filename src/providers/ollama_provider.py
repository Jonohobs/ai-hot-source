"""Ollama local model provider."""

from __future__ import annotations

import json
import time
import urllib.request

from .base import CompletionResult, ModelInfo, Provider

# Common local models — costs are always 0
OLLAMA_MODELS = [
    ModelInfo("llama3.2", "ollama", 128_000, 0.0, 0.0, tags=["local", "free"]),
    ModelInfo("phi4-mini", "ollama", 128_000, 0.0, 0.0, tags=["local", "free", "fast"]),
    ModelInfo("codellama", "ollama", 16_000, 0.0, 0.0, tags=["local", "free", "code"]),
    ModelInfo("mistral", "ollama", 32_000, 0.0, 0.0, tags=["local", "free"]),
]


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def models(self) -> list[ModelInfo]:
        return OLLAMA_MODELS

    def _is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            urllib.request.urlopen(req, timeout=2)
            return True
        except Exception:
            return False

    def complete(self, model: str, messages: list[dict[str, str]],
                 temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> CompletionResult:
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        start = time.perf_counter()
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        elapsed = (time.perf_counter() - start) * 1000

        content = data.get("message", {}).get("content", "")
        tokens_in = data.get("prompt_eval_count", 0)
        tokens_out = data.get("eval_count", 0)

        return CompletionResult(
            content=content,
            model=model,
            provider=self.name,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=elapsed,
            cost_usd=0.0,
            raw=data,
        )
