"""Tests for the quality gate."""

import unittest

from src.quality.gate import QualityGate, QualityVerdict


class TestQualityGate(unittest.TestCase):
    def setUp(self):
        self.gate = QualityGate(min_length=20)

    def test_pass_normal_response(self):
        r = self.gate.check("Here is a detailed explanation of how the function works.", "code")
        self.assertTrue(r.passed)

    def test_fail_empty(self):
        r = self.gate.check("", "code")
        self.assertEqual(r.verdict, QualityVerdict.FAIL_EMPTY)

    def test_fail_whitespace(self):
        r = self.gate.check("   \n\t  ", "code")
        self.assertEqual(r.verdict, QualityVerdict.FAIL_EMPTY)

    def test_fail_too_short_for_code(self):
        r = self.gate.check("Yes.", "code")
        self.assertEqual(r.verdict, QualityVerdict.FAIL_TOO_SHORT)

    def test_pass_short_for_quick(self):
        r = self.gate.check("Yes.", "quick")
        self.assertTrue(r.passed)

    def test_fail_greeting(self):
        r = self.gate.check("Hello! How can I help you today?", "quick")
        self.assertEqual(r.verdict, QualityVerdict.FAIL_GREETING)

    def test_fail_greeting_variant(self):
        r = self.gate.check("Sure, I'd be happy to help you with that!", "quick")
        self.assertEqual(r.verdict, QualityVerdict.FAIL_GREETING)

    def test_fail_refusal(self):
        r = self.gate.check("I cannot help with that request.", "code")
        self.assertEqual(r.verdict, QualityVerdict.FAIL_REFUSAL)

    def test_fail_repetition(self):
        repeated = "The answer is 42. " * 5
        r = self.gate.check(repeated, "code")
        self.assertEqual(r.verdict, QualityVerdict.FAIL_REPETITION)

    def test_fail_json(self):
        r = self.gate.check("{ invalid json here }", "code", expect_json=True)
        self.assertEqual(r.verdict, QualityVerdict.FAIL_JSON)

    def test_pass_valid_json(self):
        r = self.gate.check('{"key": "value", "num": 42}', "code", expect_json=True)
        self.assertTrue(r.passed)


if __name__ == "__main__":
    unittest.main()
