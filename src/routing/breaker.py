"""Circuit breaker — per-model failure tracking.

States:
  CLOSED  → normal operation, failures counted
  OPEN    → model is down, all requests rejected immediately
  HALF_OPEN → cooldown expired, probe with 1 request

Transitions:
  CLOSED → OPEN when fail_count >= threshold in rolling window
  OPEN → HALF_OPEN when now >= next_probe_at
  HALF_OPEN → CLOSED on success (success_streak >= recovery_threshold)
  HALF_OPEN → OPEN on failure (reset cooldown)
"""

from __future__ import annotations

import time

from ..store.db import HotSauceDB

FAIL_THRESHOLD = 3
COOLDOWN_SECONDS = 60.0
RECOVERY_SUCCESSES = 2


class CircuitBreaker:
    def __init__(self, db: HotSauceDB, fail_threshold: int = FAIL_THRESHOLD,
                 cooldown: float = COOLDOWN_SECONDS, recovery: int = RECOVERY_SUCCESSES):
        self.db = db
        self.fail_threshold = fail_threshold
        self.cooldown = cooldown
        self.recovery = recovery

    def state(self, model: str) -> str:
        """Get current breaker state, auto-transitioning OPEN → HALF_OPEN if cooldown elapsed."""
        rec = self.db.get_breaker(model)
        if rec is None:
            return "closed"

        if rec["state"] == "open" and rec["next_probe_at"] and time.time() >= rec["next_probe_at"]:
            self.db.upsert_breaker(model, "half_open", fail_count=rec["fail_count"],
                                   success_streak=0, opened_at=rec["opened_at"])
            return "half_open"

        return rec["state"]

    def is_available(self, model: str) -> bool:
        """Can we send a request to this model right now?"""
        s = self.state(model)
        return s in ("closed", "half_open")

    def record_success(self, model: str):
        """Record a successful call."""
        rec = self.db.get_breaker(model)
        if rec is None:
            self.db.upsert_breaker(model, "closed", fail_count=0, success_streak=1)
            return

        new_streak = rec["success_streak"] + 1

        if rec["state"] == "half_open" and new_streak >= self.recovery:
            # Recovered — close the breaker
            self.db.upsert_breaker(model, "closed", fail_count=0, success_streak=0)
        else:
            self.db.upsert_breaker(
                model, rec["state"], fail_count=max(0, rec["fail_count"] - 1),
                success_streak=new_streak,
                opened_at=rec["opened_at"],
                next_probe_at=rec["next_probe_at"],
            )

    def record_failure(self, model: str):
        """Record a failed call, potentially tripping the breaker."""
        rec = self.db.get_breaker(model)
        now = time.time()

        if rec is None:
            if 1 >= self.fail_threshold:
                self._trip(model, 1, now)
            else:
                self.db.upsert_breaker(model, "closed", fail_count=1, success_streak=0)
            return

        new_fails = rec["fail_count"] + 1

        if rec["state"] == "half_open":
            # Probe failed — back to open
            self._trip(model, new_fails, now)
        elif rec["state"] == "closed" and new_fails >= self.fail_threshold:
            self._trip(model, new_fails, now)
        else:
            self.db.upsert_breaker(
                model, rec["state"], fail_count=new_fails, success_streak=0,
                opened_at=rec.get("opened_at"), next_probe_at=rec.get("next_probe_at"),
            )

    def _trip(self, model: str, fail_count: int, now: float):
        """Trip breaker to OPEN."""
        self.db.upsert_breaker(
            model, "open", fail_count=fail_count, success_streak=0,
            opened_at=now, next_probe_at=now + self.cooldown,
        )

    def reset(self, model: str):
        """Manually reset a breaker."""
        self.db.upsert_breaker(model, "closed", fail_count=0, success_streak=0)
