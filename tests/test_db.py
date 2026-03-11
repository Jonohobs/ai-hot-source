"""Tests for the SQLite persistence layer."""

import unittest

from src.store.db import HotSauceDB


class TestHotSauceDB(unittest.TestCase):
    def setUp(self):
        self.db = HotSauceDB(":memory:")

    def tearDown(self):
        self.db.close()

    def test_create_session(self):
        sid = self.db.create_session({"project": "test"})
        self.assertIsNotNone(sid)
        session = self.db.get_session(sid)
        self.assertIsNotNone(session)

    def test_log_and_get_turns(self):
        sid = self.db.create_session()
        self.db.log_turn(sid, "user", "hello")
        self.db.log_turn(sid, "assistant", "hi there", model="test-model")
        turns = self.db.get_turns(sid)
        self.assertEqual(len(turns), 2)
        self.assertEqual(turns[0]["role"], "user")
        self.assertEqual(turns[1]["model"], "test-model")

    def test_health_logging(self):
        self.db.log_health("test-model", "test", True, 150.0)
        self.db.log_health("test-model", "test", True, 200.0)
        self.db.log_health("test-model", "test", False, error_type="Timeout")
        stats = self.db.get_model_stats("test-model")
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["successes"], 2)
        self.assertAlmostEqual(stats["success_rate"], 2/3, places=2)

    def test_breaker_upsert(self):
        self.db.upsert_breaker("test-model", "closed", fail_count=0)
        rec = self.db.get_breaker("test-model")
        self.assertEqual(rec["state"], "closed")
        # Update
        self.db.upsert_breaker("test-model", "open", fail_count=3)
        rec = self.db.get_breaker("test-model")
        self.assertEqual(rec["state"], "open")
        self.assertEqual(rec["fail_count"], 3)

    def test_nonexistent_session(self):
        self.assertIsNone(self.db.get_session("nonexistent"))

    def test_empty_stats(self):
        stats = self.db.get_model_stats("never-seen")
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["success_rate"], 1.0)  # optimistic default


if __name__ == "__main__":
    unittest.main()
