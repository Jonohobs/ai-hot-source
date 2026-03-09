"""Scoring-based model router.

Replaces the static markdown routing table with weighted scoring.
Each model gets a composite score based on:
  - capability_fit: does this model match the task's needs?
  - latency: historical p95 latency (lower is better)
  - cost: cost per 1k tokens (lower is better)
  - reliability: recent success rate from health telemetry
  - breaker_penalty: heavy penalty if breaker is open

The highest-scoring available model wins.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..providers.base import ModelInfo
from ..store.db import HotSauceDB
from .breaker import CircuitBreaker

if TYPE_CHECKING:
    from ..providers.base import Provider


@dataclass
class TaskProfile:
    """Classified task for routing decisions."""
    task_type: str  # "code", "reasoning", "quick", "vision", "creative"
    estimated_tokens: int = 1000
    needs_tools: bool = False
    needs_vision: bool = False
    explicit_model: str | None = None  # user override e.g. @gemini


# Tag-to-task affinity scores (0.0 to 1.0)
TAG_AFFINITY = {
    "code":      {"code": 1.0, "reasoning": 0.6, "quick": 0.3, "vision": 0.2, "creative": 0.3},
    "reasoning": {"code": 0.5, "reasoning": 1.0, "quick": 0.2, "vision": 0.3, "creative": 0.6},
    "fast":      {"code": 0.4, "reasoning": 0.2, "quick": 1.0, "vision": 0.4, "creative": 0.5},
    "cheap":     {"code": 0.3, "reasoning": 0.1, "quick": 0.8, "vision": 0.3, "creative": 0.4},
    "local":     {"code": 0.3, "reasoning": 0.2, "quick": 0.5, "vision": 0.0, "creative": 0.3},
    "free":      {"code": 0.4, "reasoning": 0.3, "quick": 0.9, "vision": 0.4, "creative": 0.5},
}

# Scoring weights
W_CAPABILITY = 0.35
W_LATENCY = 0.15
W_COST = 0.25
W_RELIABILITY = 0.20
W_BREAKER = 0.50  # additive penalty


def classify_task(user_message: str) -> TaskProfile:
    """Simple heuristic intent classifier. Replace with LLM classifier for production."""
    msg = user_message.lower()

    # Check for explicit model override
    explicit = None
    override_match = re.search(r"@(\w+)", user_message)
    if override_match:
        explicit = override_match.group(1)

    needs_vision = any(kw in msg for kw in ["image", "screenshot", "picture", "photo", "diagram"])
    needs_tools = any(kw in msg for kw in ["search the web", "search for", "browse", "fetch url", "run command", "execute command"])

    # Task classification
    code_signals = ["code", "function", "bug", "error", "debug", "refactor", "implement",
                    "class ", "def ", "```", "syntax", "compile", "test"]
    reasoning_signals = ["explain", "why", "analyse", "compare", "trade-off", "design",
                         "architect", "plan", "strategy", "evaluate"]
    quick_signals = ["what is", "define", "tldr", "summarise", "summary", "list", "name"]

    code_score = sum(1 for s in code_signals if s in msg)
    reasoning_score = sum(1 for s in reasoning_signals if s in msg)
    quick_score = sum(1 for s in quick_signals if s in msg)

    if needs_vision:
        task_type = "vision"
    elif code_score > reasoning_score and code_score > quick_score:
        task_type = "code"
    elif reasoning_score > quick_score:
        task_type = "reasoning"
    elif quick_score > 0:
        task_type = "quick"
    else:
        task_type = "quick"  # default to cheapest

    estimated = 500 if task_type == "quick" else 2000 if task_type == "code" else 1500

    return TaskProfile(
        task_type=task_type,
        estimated_tokens=estimated,
        needs_tools=needs_tools,
        needs_vision=needs_vision,
        explicit_model=explicit,
    )


def _capability_score(model: ModelInfo, task: TaskProfile) -> float:
    """How well does this model fit the task?"""
    score = 0.0
    for tag in model.tags:
        affinities = TAG_AFFINITY.get(tag, {})
        score = max(score, affinities.get(task.task_type, 0.0))
    return score


def _cost_score(model: ModelInfo) -> float:
    """Normalised cost score — lower cost = higher score. Free models get 1.0."""
    avg_cost = (model.cost_per_1k_in + model.cost_per_1k_out) / 2
    if avg_cost == 0:
        return 1.0
    return min(1.0, 0.01 / avg_cost)  # 0.01/1k as reference point


def _latency_score(stats: dict) -> float:
    """Normalised latency score from health telemetry."""
    avg = stats.get("avg_latency_ms")
    if avg is None or avg == 0:
        return 0.5  # unknown — neutral
    return min(1.0, 2000 / avg)  # 2s as reference point


class ScoringRouter:
    def __init__(self, db: HotSauceDB, providers: list[Provider], breaker: CircuitBreaker):
        self.db = db
        self.providers = {p.name: p for p in providers}
        self.breaker = breaker
        self._model_registry: dict[str, tuple[ModelInfo, str]] = {}
        self._rebuild_registry()

    def _rebuild_registry(self):
        """Build flat lookup of model_name → (ModelInfo, provider_name)."""
        self._model_registry.clear()
        for provider in self.providers.values():
            for model in provider.models():
                self._model_registry[model.name] = (model, provider.name)

    def score_model(self, model: ModelInfo, task: TaskProfile) -> float:
        """Compute composite score for a model given a task."""
        # Hard filters
        if task.needs_vision and not model.supports_vision:
            return -1.0
        if task.needs_tools and not model.supports_tools:
            return -1.0
        if task.estimated_tokens > model.context_window:
            return -1.0

        cap = _capability_score(model, task)
        cost = _cost_score(model)
        stats = self.db.get_model_stats(model.name)
        lat = _latency_score(stats)
        rel = stats.get("success_rate", 1.0)

        breaker_penalty = 0.0
        if not self.breaker.is_available(model.name):
            breaker_penalty = 1.0

        score = (W_CAPABILITY * cap +
                 W_LATENCY * lat +
                 W_COST * cost +
                 W_RELIABILITY * rel -
                 W_BREAKER * breaker_penalty)

        return round(score, 4)

    def rank(self, task: TaskProfile) -> list[tuple[str, float]]:
        """Return all models ranked by score, descending."""
        scores = []
        for name, (model, provider) in self._model_registry.items():
            s = self.score_model(model, task)
            if s >= 0:
                scores.append((name, s))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def select(self, user_message: str) -> tuple[str, str, TaskProfile]:
        """Classify task and select best model. Returns (model_name, provider_name, task_profile)."""
        task = classify_task(user_message)

        # Explicit override
        if task.explicit_model:
            for name, (model, provider) in self._model_registry.items():
                if task.explicit_model.lower() in name.lower() or task.explicit_model.lower() == provider.lower():
                    if self.breaker.is_available(name):
                        return name, provider, task
            # Fall through to scoring if override not found / breaker tripped

        ranked = self.rank(task)
        if not ranked:
            raise RuntimeError("No available models for this task")

        best_name = ranked[0][0]
        _, provider = self._model_registry[best_name]
        return best_name, provider, task
