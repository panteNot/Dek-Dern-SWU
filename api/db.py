"""SQLite persistence for NEO Labs conversations.

Tables:
  conversations — id, title, agent, model, created_at, updated_at
  messages      — id, conv_id, role ('user'|'assistant'), content, agent, created_at
"""
from __future__ import annotations
import sqlite3, time, uuid
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

DB_PATH = Path(__file__).parent / "conversations.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
  id         TEXT PRIMARY KEY,
  title      TEXT NOT NULL,
  agent      TEXT NOT NULL,
  model      TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  conv_id    TEXT NOT NULL,
  role       TEXT NOT NULL,
  content    TEXT NOT NULL,
  agent      TEXT,
  created_at INTEGER NOT NULL,
  FOREIGN KEY(conv_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conv_id, created_at);
CREATE INDEX IF NOT EXISTS idx_conv_updated ON conversations(updated_at DESC);

CREATE TABLE IF NOT EXISTS audit_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  ts         INTEGER NOT NULL,
  user_email TEXT,
  action     TEXT NOT NULL,
  agent      TEXT,
  model      TEXT,
  tokens_in  INTEGER DEFAULT 0,
  tokens_out INTEGER DEFAULT 0,
  ms         INTEGER DEFAULT 0,
  meta       TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action, ts DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_email, ts DESC);
"""


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with conn() as c:
        c.executescript(SCHEMA)


def now_ms() -> int:
    return int(time.time() * 1000)


def list_conversations(limit: int = 100) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT id, title, agent, model, created_at, updated_at "
            "FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_conversation(conv_id: str) -> Optional[dict]:
    with conn() as c:
        row = c.execute(
            "SELECT id, title, agent, model, created_at, updated_at "
            "FROM conversations WHERE id = ?",
            (conv_id,),
        ).fetchone()
        if not row:
            return None
        conv = dict(row)
        msgs = c.execute(
            "SELECT id, role, content, agent, created_at "
            "FROM messages WHERE conv_id = ? ORDER BY created_at ASC, id ASC",
            (conv_id,),
        ).fetchall()
        conv["messages"] = [dict(m) for m in msgs]
        return conv


def get_history(conv_id: str) -> list[dict]:
    """Return messages in Claude API format: [{role, content}, ...]"""
    with conn() as c:
        rows = c.execute(
            "SELECT role, content FROM messages WHERE conv_id = ? "
            "ORDER BY created_at ASC, id ASC",
            (conv_id,),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]


def create_conversation(title: str, agent: str, model: str = "") -> str:
    cid = "c_" + uuid.uuid4().hex[:12]
    t = now_ms()
    with conn() as c:
        c.execute(
            "INSERT INTO conversations(id, title, agent, model, created_at, updated_at) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            (cid, title[:120], agent, model, t, t),
        )
    return cid


def append_message(conv_id: str, role: str, content: str, agent: str = "") -> int:
    t = now_ms()
    with conn() as c:
        cur = c.execute(
            "INSERT INTO messages(conv_id, role, content, agent, created_at) "
            "VALUES(?, ?, ?, ?, ?)",
            (conv_id, role, content, agent, t),
        )
        c.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (t, conv_id),
        )
        return cur.lastrowid


def delete_conversation(conv_id: str) -> bool:
    with conn() as c:
        cur = c.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        return cur.rowcount > 0


def rename_conversation(conv_id: str, title: str) -> bool:
    with conn() as c:
        cur = c.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title[:120], now_ms(), conv_id),
        )
        return cur.rowcount > 0


def log_audit(
    user_email: str | None,
    action: str,
    agent: str = "",
    model: str = "",
    tokens_in: int = 0,
    tokens_out: int = 0,
    ms: int = 0,
    meta: str = "",
) -> int:
    """Append-only audit entry. Never raises — log failure shouldn't break requests."""
    try:
        with conn() as c:
            cur = c.execute(
                "INSERT INTO audit_log(ts, user_email, action, agent, model, "
                "tokens_in, tokens_out, ms, meta) VALUES(?,?,?,?,?,?,?,?,?)",
                (now_ms(), user_email or "", action, agent, model,
                 tokens_in, tokens_out, ms, (meta or "")[:500]),
            )
            return cur.lastrowid
    except Exception:
        return 0


def audit_stats(days: int = 7) -> dict:
    """Aggregate stats for admin dashboard."""
    cutoff = now_ms() - days * 86400 * 1000
    today = now_ms() - 86400 * 1000
    with conn() as c:
        total = c.execute(
            "SELECT COUNT(*) n FROM audit_log WHERE ts >= ?", (cutoff,)
        ).fetchone()["n"]
        today_n = c.execute(
            "SELECT COUNT(*) n FROM audit_log WHERE ts >= ?", (today,)
        ).fetchone()["n"]
        by_action = c.execute(
            "SELECT action, COUNT(*) n FROM audit_log WHERE ts >= ? "
            "GROUP BY action ORDER BY n DESC", (cutoff,)
        ).fetchall()
        by_agent = c.execute(
            "SELECT agent, COUNT(*) n FROM audit_log "
            "WHERE ts >= ? AND agent != '' GROUP BY agent ORDER BY n DESC",
            (cutoff,),
        ).fetchall()
        by_model = c.execute(
            "SELECT model, COUNT(*) n, SUM(tokens_in) ti, SUM(tokens_out) tout "
            "FROM audit_log WHERE ts >= ? AND model != '' GROUP BY model",
            (cutoff,),
        ).fetchall()
        by_user = c.execute(
            "SELECT user_email, COUNT(*) n FROM audit_log "
            "WHERE ts >= ? AND user_email != '' GROUP BY user_email ORDER BY n DESC LIMIT 10",
            (cutoff,),
        ).fetchall()
        tokens = c.execute(
            "SELECT COALESCE(SUM(tokens_in),0) ti, COALESCE(SUM(tokens_out),0) tout, "
            "COALESCE(AVG(ms),0) avg_ms "
            "FROM audit_log WHERE ts >= ?", (cutoff,)
        ).fetchone()
        per_day = c.execute(
            "SELECT CAST((? - ts) / 86400000 AS INTEGER) bucket, COUNT(*) n "
            "FROM audit_log WHERE ts >= ? AND action = 'chat' "
            "GROUP BY bucket ORDER BY bucket ASC",
            (now_ms(), cutoff),
        ).fetchall()
        return {
            "window_days": days,
            "total_events": total,
            "events_today": today_n,
            "tokens_in": tokens["ti"],
            "tokens_out": tokens["tout"],
            "avg_response_ms": int(tokens["avg_ms"]),
            "by_action": [dict(r) for r in by_action],
            "by_agent": [dict(r) for r in by_agent],
            "by_model": [dict(r) for r in by_model],
            "by_user": [dict(r) for r in by_user],
            "per_day": [dict(r) for r in per_day],
        }


def audit_recent(limit: int = 50) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT ts, user_email, action, agent, model, tokens_in, tokens_out, ms, meta "
            "FROM audit_log ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


init()
