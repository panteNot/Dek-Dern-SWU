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
  user_email TEXT NOT NULL DEFAULT '',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
-- user_email index created in init() after migration to avoid
-- referencing the column before ALTER TABLE adds it on old DBs.

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

CREATE TABLE IF NOT EXISTS user_memory (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_email TEXT NOT NULL DEFAULT '',
  category   TEXT NOT NULL DEFAULT 'general',
  content    TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  pinned     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_mem_user ON user_memory(user_email, created_at DESC);
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
        # Migration: older DBs have `conversations` without user_email column.
        cols = {r["name"] for r in c.execute("PRAGMA table_info(conversations)").fetchall()}
        if "user_email" not in cols:
            c.execute("ALTER TABLE conversations ADD COLUMN user_email TEXT NOT NULL DEFAULT ''")
            # Backfill existing rows to the original single-tenant owner.
            c.execute(
                "UPDATE conversations SET user_email = ? WHERE user_email = ''",
                ("pantepante72@gmail.com",),
            )
        # Idempotent: create the per-user index after the column is guaranteed.
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_conv_user "
            "ON conversations(user_email, updated_at DESC)"
        )


def now_ms() -> int:
    return int(time.time() * 1000)


def list_conversations(user_email: str = "", limit: int = 100) -> list[dict]:
    """List conversations owned by user_email. Empty email returns nothing —
    prevents accidental cross-tenant leaks if caller forgets to pass email."""
    if not user_email:
        return []
    with conn() as c:
        rows = c.execute(
            "SELECT id, title, agent, model, user_email, created_at, updated_at "
            "FROM conversations WHERE user_email = ? "
            "ORDER BY updated_at DESC LIMIT ?",
            (user_email, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_conversation(conv_id: str, user_email: str = "") -> Optional[dict]:
    """Fetch conv + messages. Returns None if conv doesn't exist OR belongs
    to a different user. Empty user_email also returns None (defensive)."""
    if not user_email:
        return None
    with conn() as c:
        row = c.execute(
            "SELECT id, title, agent, model, user_email, created_at, updated_at "
            "FROM conversations WHERE id = ? AND user_email = ?",
            (conv_id, user_email),
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


def create_conversation(title: str, agent: str, model: str = "", user_email: str = "") -> str:
    cid = "c_" + uuid.uuid4().hex[:12]
    t = now_ms()
    with conn() as c:
        c.execute(
            "INSERT INTO conversations(id, title, agent, model, user_email, created_at, updated_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, title[:120], agent, model, user_email or "", t, t),
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


def delete_all_conversations(user_email: str = "") -> int:
    """Wipe every conversation owned by user_email. Empty email = no-op
    (safer than wiping everything by accident)."""
    if not user_email:
        return 0
    with conn() as c:
        n = c.execute(
            "SELECT COUNT(*) n FROM conversations WHERE user_email = ?",
            (user_email,),
        ).fetchone()["n"]
        c.execute("DELETE FROM conversations WHERE user_email = ?", (user_email,))
        return n


def export_all_conversations(user_email: str = "") -> list[dict]:
    """Full dump of conversations owned by user_email."""
    if not user_email:
        return []
    with conn() as c:
        convs = c.execute(
            "SELECT id, title, agent, model, user_email, created_at, updated_at "
            "FROM conversations WHERE user_email = ? ORDER BY updated_at DESC",
            (user_email,),
        ).fetchall()
        out = []
        for row in convs:
            conv = dict(row)
            msgs = c.execute(
                "SELECT role, content, agent, created_at "
                "FROM messages WHERE conv_id = ? ORDER BY created_at ASC, id ASC",
                (conv["id"],),
            ).fetchall()
            conv["messages"] = [dict(m) for m in msgs]
            out.append(conv)
        return out


def delete_conversation(conv_id: str, user_email: str = "") -> bool:
    """Delete conv only if it belongs to user_email — blocks cross-tenant delete."""
    if not user_email:
        return False
    with conn() as c:
        cur = c.execute(
            "DELETE FROM conversations WHERE id = ? AND user_email = ?",
            (conv_id, user_email),
        )
        return cur.rowcount > 0


def search_conversations(q: str, user_email: str = "", limit: int = 50) -> list[dict]:
    """Search titles + message content within convs owned by user_email."""
    q = (q or "").strip()
    if not q or not user_email:
        return []
    needle = f"%{q}%"
    with conn() as c:
        rows = c.execute(
            """
            SELECT DISTINCT c.id, c.title, c.agent, c.model, c.user_email, c.created_at, c.updated_at
            FROM conversations c
            LEFT JOIN messages m ON m.conv_id = c.id
            WHERE c.user_email = ? AND (c.title LIKE ? OR m.content LIKE ?)
            ORDER BY c.updated_at DESC
            LIMIT ?
            """,
            (user_email, needle, needle, limit),
        ).fetchall()
        out = []
        for r in rows:
            conv = dict(r)
            snip = c.execute(
                "SELECT content FROM messages WHERE conv_id = ? AND content LIKE ? "
                "ORDER BY created_at ASC LIMIT 1",
                (conv["id"], needle),
            ).fetchone()
            if snip:
                content = snip["content"]
                idx = content.lower().find(q.lower())
                start = max(0, idx - 40)
                end = min(len(content), idx + len(q) + 80)
                prefix = "…" if start > 0 else ""
                suffix = "…" if end < len(content) else ""
                conv["snippet"] = prefix + content[start:end] + suffix
            else:
                conv["snippet"] = ""
            out.append(conv)
        return out


def rename_conversation(conv_id: str, title: str, user_email: str = "") -> bool:
    if not user_email:
        return False
    with conn() as c:
        cur = c.execute(
            "UPDATE conversations SET title = ?, updated_at = ? "
            "WHERE id = ? AND user_email = ?",
            (title[:120], now_ms(), conv_id, user_email),
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


# ============================================================
# USER MEMORY — user-managed facts injected into every /chat system prompt.
# Lite version (no vector DB): keyword-free, just list + join.
# ============================================================
MEM_MAX_ROWS = 50      # hard cap per user — keeps system prompt bounded
MEM_MAX_CONTENT = 500  # per-entry char cap


def add_memory(user_email: str, content: str, category: str = "general") -> int:
    content = (content or "").strip()[:MEM_MAX_CONTENT]
    if not content:
        return 0
    with conn() as c:
        # Enforce per-user cap: oldest-unpinned rows are trimmed first
        n = c.execute(
            "SELECT COUNT(*) n FROM user_memory WHERE user_email = ?",
            (user_email or "",),
        ).fetchone()["n"]
        if n >= MEM_MAX_ROWS:
            c.execute(
                "DELETE FROM user_memory WHERE id IN ("
                "SELECT id FROM user_memory WHERE user_email = ? AND pinned = 0 "
                "ORDER BY created_at ASC LIMIT ?)",
                (user_email or "", n - MEM_MAX_ROWS + 1),
            )
        cur = c.execute(
            "INSERT INTO user_memory(user_email, category, content, created_at) "
            "VALUES(?, ?, ?, ?)",
            (user_email or "", (category or "general")[:40], content, now_ms()),
        )
        return cur.lastrowid


def list_memory(user_email: str, limit: int = 100) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            "SELECT id, category, content, created_at, pinned "
            "FROM user_memory WHERE user_email = ? "
            "ORDER BY pinned DESC, created_at DESC LIMIT ?",
            (user_email or "", limit),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_memory(mem_id: int, user_email: str) -> bool:
    with conn() as c:
        cur = c.execute(
            "DELETE FROM user_memory WHERE id = ? AND user_email = ?",
            (mem_id, user_email or ""),
        )
        return cur.rowcount > 0


def get_memory_context(user_email: str) -> str:
    """Return a formatted block to append to an agent system prompt, or ''."""
    if not user_email:
        return ""
    rows = list_memory(user_email, limit=MEM_MAX_ROWS)
    if not rows:
        return ""
    lines = [f"- {r['content']}" for r in rows]
    return (
        "\n\n---\n"
        "**🧠 User Memory (ข้อเท็จจริงที่บอสให้จำไว้):**\n"
        + "\n".join(lines)
        + "\nใช้เป็นบริบทตอบให้ตรงกับบอสมากขึ้น — ไม่ต้องอ้างอิงตรงๆ ถ้าไม่เกี่ยว"
    )


init()
