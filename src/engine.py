"""Hot Sauce Engine — the main orchestrator.

Wires together: providers → router → breaker → quality gate → persistence.
This is what replaces "just a README".
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .providers.base import CompletionResult, Provider
from .quality.gate import QualityGate, QualityVerdict
from .routing.breaker import CircuitBreaker
from .routing.scorer import ScoringRouter, TaskProfile, classify_task
from .store.db import HotSauceDB

log = logging.getLogger("hotsauce")

MAX_RETRIES = 2  # retry once with same model, then fallback


class HotSauceEngine:
    """Main entry point. Create one, call .chat()."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        providers: list[Provider] | None = None,
    ):
        self.db = HotSauceDB(db_path)
        self.gate = QualityGate()

        # Default to empty — user adds providers they have keys for
        self._providers: list[Provider] = providers or []
        self.breaker = CircuitBreaker(self.db)
        self.router = ScoringRouter(self.db, self._providers, self.breaker)
        self._session_id: str | None = None

    def add_provider(self, provider: Provider):
        """Add a provider at runtime."""
        self._providers.append(provider)
        self.router = ScoringRouter(self.db, self._providers, self.breaker)

    def session(self, session_id: str | None = None) -> str:
        """Start or resume a session."""
        if session_id:
            existing = self.db.get_session(session_id)
            if existing:
                self._session_id = session_id
                return session_id
        self._session_id = self.db.create_session()
        return self._session_id

    def chat(
        self,
        message: str,
        session_id: str | None = None,
        system: str | None = None,
        expect_json: bool = False,
        **kwargs,
    ) -> CompletionResult:
        """Send a message, get a quality-checked response.

        Handles: routing → call → quality gate → retry/fallback → persistence.
        """
        sid = session_id or self._session_id or self.session()

        # Log user turn
        self.db.log_turn(sid, "user", message)

        # Build messages from session history
        turns = self.db.get_turns(sid, limit=50)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        for t in turns:
            messages.append({"role": t["role"], "content": t["content"]})

        # Route
        model_name, provider_name, task = self.router.select(message)
        ranked = self.router.rank(task)
        tried_models: set[str] = set()

        for attempt in range(MAX_RETRIES + len(ranked)):
            if model_name in tried_models:
                # Move to next model in ranking
                for name, score in ranked:
                    if name not in tried_models:
                        model_name = name
                        _, provider_name = self.router._model_registry[name]
                        break
                else:
                    break  # exhausted all models

            tried_models.add(model_name)
            provider = self.router.providers.get(provider_name)
            if not provider:
                log.warning(f"Provider {provider_name} not registered, skipping {model_name}")
                continue

            try:
                result = provider.timed_complete(model_name, messages, **kwargs)

                # Record health
                self.db.log_health(model_name, provider_name, True, result.latency_ms)
                self.breaker.record_success(model_name)

                # Quality gate
                gate_result = self.gate.check(
                    result.content,
                    task_type=task.task_type,
                    expect_json=expect_json,
                )

                if gate_result.passed:
                    # Persist and return
                    self.db.log_turn(
                        sid, "assistant", result.content,
                        model=model_name, provider=provider_name,
                        latency_ms=result.latency_ms,
                        tokens_in=result.tokens_in, tokens_out=result.tokens_out,
                        cost_usd=result.cost_usd, quality_status="pass",
                    )
                    return result

                # Quality failed — log and try next model
                log.warning(f"Quality gate failed for {model_name}: {gate_result.detail}")
                self.db.log_turn(
                    sid, "assistant", result.content,
                    model=model_name, provider=provider_name,
                    latency_ms=result.latency_ms,
                    tokens_in=result.tokens_in, tokens_out=result.tokens_out,
                    cost_usd=result.cost_usd,
                    quality_status=gate_result.verdict.value,
                )
                continue

            except Exception as e:
                log.error(f"Model {model_name} failed: {e}")
                self.db.log_health(
                    model_name, provider_name, False,
                    error_type=type(e).__name__, error_message=str(e)[:500],
                )
                self.breaker.record_failure(model_name)
                continue

        raise RuntimeError(
            f"All models exhausted after {len(tried_models)} attempts. "
            f"Tried: {tried_models}"
        )

    def stats(self) -> dict[str, Any]:
        """Get current engine stats — model health, breaker states, session count."""
        result = {"models": {}, "breakers": {}}
        for name in self.router._model_registry:
            result["models"][name] = self.db.get_model_stats(name)
            breaker = self.db.get_breaker(name)
            if breaker:
                result["breakers"][name] = dict(breaker)
        return result
