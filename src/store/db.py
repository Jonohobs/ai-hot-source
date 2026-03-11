"""SQLite persistence layer for the Hot Sauce engine.

Stores sessions, turns, model health telemetry, circuit breaker state,
and eval results. Local-first — no external dependencies.
"""

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path.home() / ".agent" / "hotsauce.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS turns (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model TEXT,
    provider TEXT,
    latency_ms REAL,
    tokens_in INTEGER,
    tokens_out INTEGER,
    cost_usd REAL,
    quality_status TEXT CHECK(quality_status IN ('pass', 'fail', 'retry', 'fallback', NULL)),
    created_at REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS model_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL,
    provider TEXT NOT NULL,
    ts REAL NOT NULL,
    success INTEGER NOT NULL CHECK(success IN (0, 1)),
    latency_ms REAL,
    error_type TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS breaker_state (
    model TEXT PRIMARY KEY,
    state TEXT NOT NULL DEFAULT 'closed' CHECK(state IN ('closed', 'open', 'half_open')),
    fail_count INTEGER NOT NULL DEFAULT 0,
    success_streak INTEGER NOT NULL DEFAULT 0,
    opened_at REAL,
    next_probe_at REAL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_cases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    input_json TEXT NOT NULL,
    assertions_json TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    model TEXT NOT NULL,
    passed INTEGER NOT NULL CHECK(passed IN (0, 1)),
    metrics_json TEXT DEFAULT '{}',
    created_at REAL NOT NULL,
    FOREIGN KEY (case_id) REFERENCES eval_cases(id)
);

CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
CREATE INDEX IF NOT EXISTS idx_turns_model ON turns(model);
CREATE INDEX IF NOT EXISTS idx_health_model_ts ON model_health(model, ts);
CREATE INDEX IF NOT EXISTS idx_eval_runs_case ON eval_runs(case_id);
"""


class HotSauceDB:
    def __init__(self, db_path: Path | str | None = None):
        self._in_memory = db_path == ":memory:"
        if not self._in_memory:
            self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = None
        self._conn: sqlite3.Connection | None = None
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            target = ":memory:" if self._in_memory else str(self.db_path)
            self._conn = sqlite3.connect(target)
            self._conn.row_factory = sqlite3.Row
            if not self._in_memory:
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    @contextmanager
    def _tx(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_schema(self):
        conn = self._connect()
        conn.executescript(SCHEMA)

    def close(self):
        """Close the database connection. Call before deleting the DB file on Windows."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # -- Sessions --

    def create_session(self, metadata: dict | None = None) -> str:
        sid = str(uuid.uuid4())
        now = time.time()
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO sessions (id, created_at, updated_at, metadata_json) VALUES (?, ?, ?, ?)",
                (sid, now, now, json.dumps(metadata or {})),
            )
        return sid

    def get_session(self, session_id: str) -> dict | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

    # -- Turns --

    def log_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        model: str | None = None,
        provider: str | None = None,
        latency_ms: float | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        cost_usd: float | None = None,
        quality_status: str | None = None,
    ) -> str:
        tid = str(uuid.uuid4())
        now = time.time()
        with self._tx() as conn:
            conn.execute(
                """INSERT INTO turns
                   (id, session_id, role, content, model, provider,
                    latency_ms, tokens_in, tokens_out, cost_usd, quality_status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tid, session_id, role, content, model, provider,
                 latency_ms, tokens_in, tokens_out, cost_usd, quality_status, now),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
        return tid

    def get_turns(self, session_id: str, limit: int = 50) -> list[dict]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM turns WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # -- Model Health --

    def log_health(
        self,
        model: str,
        provider: str,
        success: bool,
        latency_ms: float | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
    ):
        with self._tx() as conn:
            conn.execute(
                """INSERT INTO model_health (model, provider, ts, success, latency_ms, error_type, error_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (model, provider, time.time(), int(success), latency_ms, error_type, error_message),
            )

    def get_model_stats(self, model: str, window_seconds: float = 300) -> dict[str, Any]:
        """Get success rate and latency stats for a model over a time window."""
        cutoff = time.time() - window_seconds
        conn = self._connect()
        row = conn.execute(
            """SELECT
                 COUNT(*) as total,
                 SUM(success) as successes,
                 AVG(CASE WHEN success = 1 THEN latency_ms END) as avg_latency,
                 MAX(CASE WHEN success = 1 THEN latency_ms END) as p_max_latency
               FROM model_health
               WHERE model = ? AND ts > ?""",
            (model, cutoff),
        ).fetchone()
        total = row["total"] or 0
        successes = row["successes"] or 0
        return {
            "model": model,
            "total": total,
            "successes": successes,
            "success_rate": successes / total if total > 0 else 1.0,
            "avg_latency_ms": row["avg_latency"],
            "max_latency_ms": row["p_max_latency"],
        }

    # -- Breaker State --

    def get_breaker(self, model: str) -> dict | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM breaker_state WHERE model = ?", (model,)).fetchone()
        return dict(row) if row else None

    def upsert_breaker(self, model: str, state: str, fail_count: int = 0,
                       success_streak: int = 0, opened_at: float | None = None,
                       next_probe_at: float | None = None):
        now = time.time()
        with self._tx() as conn:
            conn.execute(
                """INSERT INTO breaker_state (model, state, fail_count, success_streak, opened_at, next_probe_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(model) DO UPDATE SET
                     state=excluded.state, fail_count=excluded.fail_count,
                     success_streak=excluded.success_streak, opened_at=excluded.opened_at,
                     next_probe_at=excluded.next_probe_at, updated_at=excluded.updated_at""",
                (model, state, fail_count, success_streak, opened_at, next_probe_at, now),
            )
