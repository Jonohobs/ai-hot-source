"""Tests for the circuit breaker."""

import time
import unittest

from src.routing.breaker import CircuitBreaker
from src.store.db import HotSauceDB


class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.db = HotSauceDB(":memory:")
        self.breaker = CircuitBreaker(self.db, fail_threshold=3, cooldown=0.5, recovery=2)

    def tearDown(self):
        self.db.close()

    def test_starts_closed(self):
        self.assertEqual(self.breaker.state("test-model"), "closed")
        self.assertTrue(self.breaker.is_available("test-model"))

    def test_trips_after_threshold(self):
        for _ in range(3):
            self.breaker.record_failure("test-model")
        self.assertEqual(self.breaker.state("test-model"), "open")
        self.assertFalse(self.breaker.is_available("test-model"))

    def test_does_not_trip_below_threshold(self):
        self.breaker.record_failure("test-model")
        self.breaker.record_failure("test-model")
        self.assertEqual(self.breaker.state("test-model"), "closed")

    def test_transitions_to_half_open(self):
        for _ in range(3):
            self.breaker.record_failure("test-model")
        self.assertEqual(self.breaker.state("test-model"), "open")
        # Wait for cooldown
        time.sleep(0.6)
        self.assertEqual(self.breaker.state("test-model"), "half_open")
        self.assertTrue(self.breaker.is_available("test-model"))

    def test_recovers_from_half_open(self):
        for _ in range(3):
            self.breaker.record_failure("test-model")
        time.sleep(0.6)
        self.assertEqual(self.breaker.state("test-model"), "half_open")
        # Successful probes
        self.breaker.record_success("test-model")
        self.breaker.record_success("test-model")
        self.assertEqual(self.breaker.state("test-model"), "closed")

    def test_half_open_failure_reopens(self):
        for _ in range(3):
            self.breaker.record_failure("test-model")
        time.sleep(0.6)
        self.assertEqual(self.breaker.state("test-model"), "half_open")
        self.breaker.record_failure("test-model")
        self.assertEqual(self.breaker.state("test-model"), "open")

    def test_manual_reset(self):
        for _ in range(3):
            self.breaker.record_failure("test-model")
        self.assertEqual(self.breaker.state("test-model"), "open")
        self.breaker.reset("test-model")
        self.assertEqual(self.breaker.state("test-model"), "closed")


if __name__ == "__main__":
    unittest.main()
