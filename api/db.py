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


init()
