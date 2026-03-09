"""Quality gate — catch garbage responses before they reach the user.

Runs fast heuristic checks on model output:
  1. Too short (< min_length chars for non-trivial tasks)
  2. Empty or whitespace-only
  3. Greeting/filler patterns ("Hello! How can I help you today?")
  4. Refusal when none was expected
  5. Repeated text (model looping)
  6. Malformed JSON when JSON was requested

On failure: one retry with stricter prompt, then fallback to next model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class QualityVerdict(Enum):
    PASS = "pass"
    FAIL_EMPTY = "fail_empty"
    FAIL_TOO_SHORT = "fail_too_short"
    FAIL_GREETING = "fail_greeting"
    FAIL_REFUSAL = "fail_refusal"
    FAIL_REPETITION = "fail_repetition"
    FAIL_JSON = "fail_json"


@dataclass
class GateResult:
    verdict: QualityVerdict
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.verdict == QualityVerdict.PASS


# Patterns that indicate a useless "polite but empty" response
GREETING_PATTERNS = [
    r"^(hi|hello|hey)[!.,]?\s*(how can i|what can i|i'?m here to)\s*(help|assist)",
    r"^(sure|of course|absolutely)[!.,]?\s*(i'?d be happy to|let me)\s*(help|assist)",
    r"^i'?m\s+(an?\s+)?(ai|language model|assistant)",
    r"^as an ai",
]

REFUSAL_PATTERNS = [
    r"i (can'?t|cannot|am unable to|don'?t|do not) (help|assist|provide|generate|create) (with )?(that|this)",
    r"i'?m (not able|unable) to",
    r"(against|violates?) my (guidelines|policy|programming)",
    r"i (must|have to) (decline|refuse)",
]

REPETITION_THRESHOLD = 3  # same phrase repeated N+ times = looping


class QualityGate:
    def __init__(self, min_length: int = 20, max_repetition: int = REPETITION_THRESHOLD):
        self.min_length = min_length
        self.max_repetition = max_repetition

    def check(self, response: str, task_type: str = "quick",
              expect_json: bool = False) -> GateResult:
        """Run all quality checks. Returns first failure or PASS."""

        # 1. Empty
        stripped = response.strip()
        if not stripped:
            return GateResult(QualityVerdict.FAIL_EMPTY, "Response is empty")

        # 2. Too short (skip for "quick" tasks where short answers are valid)
        if task_type != "quick" and len(stripped) < self.min_length:
            return GateResult(QualityVerdict.FAIL_TOO_SHORT,
                              f"Response too short ({len(stripped)} chars, min {self.min_length})")

        # 3. Greeting/filler
        lower = stripped.lower()
        for pattern in GREETING_PATTERNS:
            if re.search(pattern, lower):
                return GateResult(QualityVerdict.FAIL_GREETING,
                                  f"Response is filler/greeting: {stripped[:80]}")

        # 4. Unexpected refusal
        for pattern in REFUSAL_PATTERNS:
            if re.search(pattern, lower):
                return GateResult(QualityVerdict.FAIL_REFUSAL,
                                  f"Model refused: {stripped[:80]}")

        # 5. Repetition detection
        # Split into sentences, check for loops
        sentences = re.split(r'[.!?\n]+', stripped)
        sentences = [s.strip().lower() for s in sentences if len(s.strip()) > 10]
        if sentences:
            from collections import Counter
            counts = Counter(sentences)
            most_common_count = counts.most_common(1)[0][1] if counts else 0
            if most_common_count >= self.max_repetition:
                return GateResult(QualityVerdict.FAIL_REPETITION,
                                  f"Repeated phrase {most_common_count}x")

        # 6. JSON validation
        if expect_json:
            import json
            try:
                json.loads(stripped)
            except json.JSONDecodeError as e:
                return GateResult(QualityVerdict.FAIL_JSON,
                                  f"Invalid JSON: {e}")

        return GateResult(QualityVerdict.PASS)
