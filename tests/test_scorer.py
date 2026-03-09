"""Tests for the scoring router."""

import unittest

from src.providers.base import ModelInfo, Provider, CompletionResult
from src.routing.breaker import CircuitBreaker
from src.routing.scorer import ScoringRouter, TaskProfile, classify_task
from src.store.db import HotSauceDB


class FakeProvider(Provider):
    name = "fake"

    def __init__(self, model_list: list[ModelInfo]):
        self._models = model_list

    def models(self) -> list[ModelInfo]:
        return self._models

    def complete(self, model, messages, **kwargs) -> CompletionResult:
        return CompletionResult("fake", model, "fake", 10, 10, 100.0, 0.0)


class TestClassifyTask(unittest.TestCase):
    def test_code_task(self):
        t = classify_task("fix this bug in the function")
        self.assertEqual(t.task_type, "code")

    def test_reasoning_task(self):
        t = classify_task("explain why this architecture is better")
        self.assertEqual(t.task_type, "reasoning")

    def test_quick_task(self):
        t = classify_task("what is a monad")
        self.assertEqual(t.task_type, "quick")

    def test_vision_task(self):
        t = classify_task("describe this screenshot")
        self.assertEqual(t.task_type, "vision")

    def test_explicit_override(self):
        t = classify_task("@gemini explain this error")
        self.assertEqual(t.explicit_model, "gemini")

    def test_tools_needed(self):
        t = classify_task("search for recent papers on transformers")
        self.assertTrue(t.needs_tools)


class TestScoringRouter(unittest.TestCase):
    def setUp(self):
        self.db = HotSauceDB(":memory:")
        self.breaker = CircuitBreaker(self.db)

        self.cheap = ModelInfo("cheap-fast", "fake", 128_000, 0.0, 0.0, tags=["fast", "cheap", "free"])
        self.coder = ModelInfo("code-heavy", "fake", 200_000, 0.01, 0.04, supports_tools=True, tags=["code", "reasoning"])
        self.vision = ModelInfo("vision-model", "fake", 128_000, 0.005, 0.02, supports_vision=True, tags=["fast"])

        self.provider = FakeProvider([self.cheap, self.coder, self.vision])
        self.router = ScoringRouter(self.db, [self.provider], self.breaker)

    def tearDown(self):
        self.db.close()

    def test_code_task_prefers_coder(self):
        task = TaskProfile("code", estimated_tokens=1000)
        ranked = self.router.rank(task)
        names = [n for n, _ in ranked]
        self.assertEqual(names[0], "code-heavy")

    def test_quick_task_prefers_cheap(self):
        task = TaskProfile("quick", estimated_tokens=100)
        ranked = self.router.rank(task)
        names = [n for n, _ in ranked]
        self.assertEqual(names[0], "cheap-fast")

    def test_vision_filters_non_vision(self):
        task = TaskProfile("vision", needs_vision=True)
        ranked = self.router.rank(task)
        names = [n for n, _ in ranked]
        self.assertIn("vision-model", names)
        self.assertNotIn("cheap-fast", names)
        self.assertNotIn("code-heavy", names)

    def test_breaker_penalises(self):
        task = TaskProfile("quick", estimated_tokens=100)
        # Trip the cheap model's breaker
        for _ in range(3):
            self.breaker.record_failure("cheap-fast")
        ranked = self.router.rank(task)
        names = [n for n, _ in ranked]
        # cheap-fast should no longer be first
        self.assertNotEqual(names[0], "cheap-fast")

    def test_select_returns_valid(self):
        model, provider, task = self.router.select("what is python")
        self.assertIn(model, ["cheap-fast", "code-heavy", "vision-model"])
        self.assertEqual(provider, "fake")


if __name__ == "__main__":
    unittest.main()
