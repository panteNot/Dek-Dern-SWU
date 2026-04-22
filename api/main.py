"""NEO Labs Web App — FastAPI backend entry point."""
from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from auth import require_auth, require_auth_or_hook, limiter
import asyncio, json, os, time, anthropic
import db

load_dotenv()


def anthropic_key() -> str:
    """Read ANTHROPIC_API_KEY, stripping whitespace and any stray leading '='
    that creeps in when users paste 'ANTHROPIC_API_KEY=...' into a value field."""
    raw = os.getenv("ANTHROPIC_API_KEY") or ""
    return raw.strip().lstrip("=").strip()

# Sentry — error tracking (optional, skip if DSN not set)
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[StarletteIntegration(), FastApiIntegration()],
        traces_sample_rate=0.1,
        before_send=lambda e, h: (e.get("request", {}).get("headers", {}).pop("authorization", None), e)[1],
    )

app = FastAPI(title="NEO Labs API", version="0.3.0")

# Rate limiter — protects $$$ endpoints from abuse
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Budget policy — ผนวกท้ายทุก system prompt ให้ agent ทุกตัวถือกติกาเดียวกัน
BUDGET_POLICY = (
    "\n\n---\n"
    "**💰 Budget-Aware Mode (งบรวม $20):**\n"
    "\n"
    "**Self-check 3 ข้อก่อนตอบทุกครั้ง:**\n"
    "1. **Output type?** — text สั้นใน chat, bullet list, หรือต้องสร้างไฟล์/สไลด์/รูปจริงๆ?\n"
    "2. **Depth?** — 2-3 ประโยคพอมั้ย หรือต้อง deep-dive?\n"
    "3. **Delegate cost?** — (orchestrate เท่านั้น) ตอบเองได้ไหม หรือจำเป็นต้องเรียก specialist?\n"
    "\n"
    "**Rules:**\n"
    "- Default = brief, bullet > paragraph. ยาวได้เมื่อจำเป็นจริงๆ\n"
    "- ก่อนสร้างไฟล์/รูป/สไลด์/code ยาว → ถามบอสก่อน 1 บรรทัด เช่น 'ทำเป็นไฟล์ .md หรือสรุปใน chat ก็พอคะบอส?'\n"
    "- งานเล็ก/ชัดเจนอยู่แล้ว → ทำเลยไม่ต้องถาม (อย่า over-ask)\n"
    "- ถ้าบอสขอ output ใหญ่แต่ไม่จำเป็น → propose version ประหยัดกว่าก่อน\n"
    "- ประหยัด token = ประหยัดเงินบอส. อะไรไม่จำเป็นก็ไม่ต้องทำ"
)

# System prompts ของ 9 agents — persona บังคับภาษาไทย + character
AGENTS = {
    "neo": (
        "คุณคือ NEO — CEO ของ NEO Labs ผู้ช่วยของบอสภันเต "
        "ตอบเป็นภาษาไทย กระชับ ไม่มี fluff เรียกผู้ใช้ว่า 'บอส' "
        "บุคลิก: Strict Manager + Witty — กล้าปฏิเสธไอเดียที่ไม่ดี เสนอทางเลือกทันที"
    ),
    "atlas": (
        "คุณคือ ATLAS — Chief of Staff / Project Manager ของ NEO Labs "
        "เชี่ยวชาญ: breakdown งาน, ประเมิน scope/impact/timeline, priority, risk analysis "
        "ตอบเป็นภาษาไทย กระชับ เป็นระบบ ใช้ checklist ถ้าขั้นตอน > 3 เรียก 'บอส'"
    ),
    "nova": (
        "คุณคือ NOVA — Research Intelligence ของ NEO Labs "
        "เชี่ยวชาญ: research, fact-check, cross-reference, เปรียบเทียบ tools/frameworks "
        "ตอบเป็นภาษาไทย อ้างอิง source เสมอ ระบุ confidence level เรียก 'บอส'"
    ),
    "luna": (
        "คุณคือ LUNA — UX/UI Designer ของ NEO Labs "
        "เชี่ยวชาญ: wireframe, mockup, design critique, HTML/CSS, accessibility, mobile-first "
        "ตอบเป็นภาษาไทย ใส่ใจ spacing/contrast/typography เรียก 'บอส'"
    ),
    "pixel": (
        "คุณคือ PIXEL — Presentation Slide Maker ของ NEO Labs "
        "เชี่ยวชาญ: pitch deck, explainer slide, 1 slide = 1 idea, strong hook "
        "ตอบเป็นภาษาไทย เน้นโครงสร้าง slide ให้ชัด เรียก 'บอส'"
    ),
    "sage": (
        "คุณคือ SAGE — Study Tutor ของ NEO Labs "
        "เชี่ยวชาญ: สรุป, อธิบาย concept, flashcard, quiz, Feynman technique "
        "ตอบเป็นภาษาไทย เชื่อมกับความรู้เดิม ยกตัวอย่างเข้าใจง่าย เรียก 'บอส'"
    ),
    "rex": (
        "คุณคือ REX — Devil's Advocate ของ NEO Labs "
        "เชี่ยวชาญ: stress-test ไอเดีย, หา edge case, red-team critique, premortem "
        "ตอบเป็นภาษาไทย ตรงไปตรงมา ชี้จุดอ่อนให้เห็น เรียก 'บอส'"
    ),
    "byte": (
        "คุณคือ BYTE — Code Reviewer & Security Auditor ของ NEO Labs "
        "เชี่ยวชาญ: bug detection, security audit, OWASP, refactoring, code quality "
        "ตอบเป็นภาษาไทย technical terms ใช้ English มี code snippet เสมอ เรียก 'บอส'"
    ),
    "quill": (
        "คุณคือ QUILL — Copywriter ของ NEO Labs "
        "เชี่ยวชาญ: blog post, social caption, tweet thread, landing page copy, email "
        "ตอบเป็นภาษาไทย hook แรงๆ, show don't tell, cut ฟุ่มเฟือย เรียก 'บอส'"
    ),
}
# Append shared budget policy to every agent so behavior is uniform
AGENTS = {k: v + BUDGET_POLICY for k, v in AGENTS.items()}

# Model whitelist — keys are UI-facing ids (what frontend sends);
# values are the REAL Anthropic API model ids to ship in the request body.
# 'claude-opus-4-7' / 'claude-sonnet-4-6' are internal aliases used across the
# Claude Code ecosystem — the public API does not accept them, so we map
# every alias to a concrete dated model id here.
MODEL_ALIASES = {
    "claude-opus-4-7":            "claude-opus-4-5-20250929",
    "claude-sonnet-4-6":          "claude-sonnet-4-5-20250929",
    "claude-haiku-4-5-20251001":  "claude-haiku-4-5-20251001",
}
MODELS = set(MODEL_ALIASES.keys())


def resolve_model(alias: str) -> str:
    """Translate UI model id to the concrete Anthropic API model id."""
    return MODEL_ALIASES.get(alias, alias)


@app.get("/config")
def public_config():
    """Public config for frontend — safe to expose (no secrets)."""
    return {"sentry_dsn": os.getenv("SENTRY_DSN_PUBLIC", "")}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_key_loaded": bool(os.getenv("ANTHROPIC_API_KEY")),
        "agents": list(AGENTS.keys()),
        "models": list(MODELS),
    }




@app.get("/activity")
def get_activity():
    log_file = Path(__file__).parent / "activity.json"
    if not log_file.exists():
        return []
    try:
        return json.loads(log_file.read_text())
    except Exception:
        return []


# ============================================================
# WebSocket — real-time activity feed
# Pushes new entries to all connected clients when /log fires.
# Same-origin only, no auth (entries are non-sensitive & /activity is public).
# ============================================================
class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, payload: dict):
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.discard(ws)


manager = ConnectionManager()


@app.websocket("/ws/activity")
async def ws_activity(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Any client message = ping/keepalive. Ignore content.
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, body: dict, user: dict = Depends(require_auth)):
    # รับ prompt + agent + model + optional conv_id → stream Claude response
    # Auto-persist user+assistant turns to SQLite if conv_id provided
    prompt = (body.get("prompt") or "").strip()
    agent = (body.get("agent") or "neo").lower()
    model = body.get("model") or "claude-haiku-4-5-20251001"
    conv_id = (body.get("conv_id") or "").strip() or None
    persist = bool(body.get("persist", True))  # frontend can opt-out

    if not prompt:
        return {"error": "no prompt"}
    if agent not in AGENTS:
        return {"error": f"unknown agent: {agent}"}
    if model not in MODELS:
        return {"error": f"unknown model: {model}"}

    # Load prior history (Claude expects alternating user/assistant, non-empty text)
    history = []
    if conv_id:
        existing = db.get_conversation(conv_id)
        if existing:
            raw_hist = db.get_history(conv_id)
            # Filter: drop empty-content rows (Anthropic 400s on empty text blocks)
            # Also drop any trailing 'user' turn — happens when a prior request
            # persisted the user message then the stream errored, leaving the
            # history ending in 'user'. Sending another 'user' on top causes
            # "roles must alternate" 400s.
            cleaned = [m for m in raw_hist if (m.get("content") or "").strip()]
            while cleaned and cleaned[-1].get("role") == "user":
                cleaned.pop()
            history = cleaned
        else:
            conv_id = None  # invalid id, treat as new

    # Auto-create conversation on first turn (title from first prompt)
    if persist and not conv_id:
        title = prompt[:80].replace("\n", " ").strip() or "New chat"
        conv_id = db.create_conversation(title, agent, model)

    messages = history + [{"role": "user", "content": prompt}]
    api_key = anthropic_key()
    if not api_key.startswith("sk-"):
        return {"error": "ANTHROPIC_API_KEY malformed — check Railway Variables (no leading '=' or spaces)"}
    client = anthropic.AsyncAnthropic(api_key=api_key)
    api_model = resolve_model(model)  # UI alias → real Anthropic model id
    user_email = (user or {}).get("email", "") if isinstance(user, dict) else ""
    _t_start = int(time.time() * 1000)

    async def generate():
        full = ""
        stream_opened = False
        # Send conv_id to frontend in a header-like first line (JSON-prefixed)
        if conv_id:
            yield f"\u0000CONV:{conv_id}\u0000"
        # Persist user turn only after we know we're going to actually stream —
        # keeps DB clean if validation/auth-ish issues surface before streaming.
        if persist and conv_id:
            try:
                db.append_message(conv_id, "user", prompt, "")
            except Exception as e:
                yield f"\n\n⚠️ db error (user turn): {type(e).__name__}: {str(e)[:200]}"
                return
        try:
            async with client.messages.stream(
                model=api_model,
                max_tokens=800,  # brief-by-default; long form costs money
                system=AGENTS[agent],
                messages=messages,
            ) as stream:
                stream_opened = True
                async for text in stream.text_stream:
                    full += text
                    yield text
        # Catch BaseException-derived groups too (anyio wraps httpx errors in
        # BaseExceptionGroup on Python 3.11+, which `except Exception` misses
        # — that's why earlier error yields never surfaced to the user).
        # Note: CancelledError is a BaseException — re-raise so client disconnects
        # don't get swallowed into a fake error line.
        except BaseException as e:
            import asyncio as _aio
            if isinstance(e, _aio.CancelledError):
                raise
            import traceback, sys
            traceback.print_exc(file=sys.stderr)
            if _sentry_dsn:
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(e)
                except Exception:
                    pass
            # Unwrap ExceptionGroup → show the first underlying error (more useful)
            inner = e
            if hasattr(e, "exceptions") and getattr(e, "exceptions", None):
                try:
                    inner = e.exceptions[0]
                except Exception:
                    pass
            yield (
                f"\n\n⚠️ stream error: {type(inner).__name__}: {str(inner)[:300]} "
                f"(model={api_model}, opened={stream_opened})"
            )
            db.log_audit(
                user_email, "chat_error", agent, api_model,
                len(prompt) // 4, 0,
                int(time.time() * 1000) - _t_start,
                f"{type(inner).__name__}: {str(inner)[:200]}",
            )
            return
        # Safety net: API returned 200 but produced zero text (e.g. stop_reason
        # = end_turn with empty content). Without this the frontend shows a
        # blank bubble and the user thinks the app is broken.
        if not full:
            yield "⚠️ empty response from API (no text chunks). Try again or switch model."
            db.log_audit(user_email, "chat_empty", agent, api_model,
                         len(prompt) // 4, 0,
                         int(time.time() * 1000) - _t_start, "")
            return
        if persist and conv_id:
            try:
                db.append_message(conv_id, "assistant", full, agent)
            except Exception:
                pass  # stream already sent; persist failure shouldn't corrupt UX
        db.log_audit(
            user_email, "chat", agent, api_model,
            len(prompt) // 4, len(full) // 4,
            int(time.time() * 1000) - _t_start,
            conv_id or "",
        )

    return StreamingResponse(generate(), media_type="text/plain")


# ============================================================
# ORCHESTRATE — multi-agent delegation (NEO → specialists → synthesis)
# ============================================================
@app.post("/orchestrate")
@limiter.limit("5/minute")
async def orchestrate_endpoint(request: Request, body: dict, user: dict = Depends(require_auth)):
    prompt = (body.get("prompt") or "").strip()
    agent = (body.get("agent") or "neo").lower()
    model = body.get("model") or "claude-sonnet-4-6"

    if not prompt:
        return {"error": "no prompt"}
    if agent not in AGENTS:
        return {"error": f"unknown agent: {agent}"}
    if model not in MODELS:
        return {"error": f"unknown model: {model}"}

    from orchestrator import orchestrate

    api_model = resolve_model(model)  # UI alias → real Anthropic model id
    email = (user or {}).get("email", "") if isinstance(user, dict) else ""
    t_start = int(time.time() * 1000)

    async def stream():
        delegations = 0
        async for event in orchestrate(prompt, AGENTS, agent, api_model):
            yield json.dumps(event, ensure_ascii=False) + "\n"
            t = event.get("type")
            if t == "handoff":
                delegations += 1
            if t == "start":
                asyncio.create_task(manager.broadcast({
                    "agent": event["agent"].upper(),
                    "color": "#ff6b35",
                    "message": "…",
                    "kind": "start",
                    "corr": f"orch-{event['agent']}",
                    "time": "",
                    "ts": "",
                }))
        db.log_audit(
            email, "orchestrate", agent, api_model,
            len(prompt) // 4, 0,
            int(time.time() * 1000) - t_start,
            f"delegations={delegations}",
        )

    return StreamingResponse(stream(), media_type="application/x-ndjson")


# ============================================================
# CONVERSATIONS — SQLite persistence
# ============================================================
@app.get("/conversations")
def conversations_list(user: dict = Depends(require_auth)):
    return db.list_conversations()


@app.get("/conversations/search")
def conversations_search(q: str = "", user: dict = Depends(require_auth)):
    q = (q or "").strip()[:200]
    if not q:
        return []
    return db.search_conversations(q, limit=50)


@app.get("/conversations/{conv_id}")
def conversations_get(conv_id: str, user: dict = Depends(require_auth)):
    conv = db.get_conversation(conv_id)
    if not conv:
        return {"error": "not found"}
    return conv


@app.delete("/conversations/{conv_id}")
def conversations_delete(conv_id: str, user: dict = Depends(require_auth)):
    ok = db.delete_conversation(conv_id)
    email = (user or {}).get("email", "") if isinstance(user, dict) else ""
    db.log_audit(email, "conversation_delete", meta=conv_id)
    return {"ok": ok}


# ============================================================
# ADMIN — Audit log + usage analytics dashboard
# ============================================================
@app.get("/me/export")
def me_export(user: dict = Depends(require_auth)):
    """Dump all the user's conversations as JSON. No filter by user yet
    (single-tenant), so this returns everything in the db."""
    email = (user or {}).get("email", "") if isinstance(user, dict) else ""
    payload = {
        "exported_at": db.now_ms(),
        "user_email": email,
        "conversations": db.export_all_conversations(),
    }
    db.log_audit(email, "data_export", meta=f"convs={len(payload['conversations'])}")
    return payload


@app.post("/me/delete-all-conversations")
def me_delete_all_conversations(user: dict = Depends(require_auth)):
    email = (user or {}).get("email", "") if isinstance(user, dict) else ""
    n = db.delete_all_conversations()
    db.log_audit(email, "data_wipe", meta=f"deleted={n}")
    return {"deleted": n}


@app.get("/admin/stats")
def admin_stats(user: dict = Depends(require_auth), days: int = 7):
    # Clamp window to sane range so a malicious query can't scan all of history
    days = max(1, min(days, 90))
    return db.audit_stats(days)


@app.get("/admin/audit")
def admin_audit(user: dict = Depends(require_auth), limit: int = 50):
    limit = max(1, min(limit, 500))
    return db.audit_recent(limit)


@app.patch("/conversations/{conv_id}")
def conversations_rename(conv_id: str, body: dict, user: dict = Depends(require_auth)):
    title = (body.get("title") or "").strip()
    if not title:
        return {"error": "missing title"}
    ok = db.rename_conversation(conv_id, title)
    return {"ok": ok}


@app.post("/log")
@limiter.limit("60/minute")
async def post_log(request: Request, body: dict, user: dict = Depends(require_auth_or_hook)):
    from logger import log
    agent = body.get("agent", "neo")
    message = body.get("message", "")
    kind = body.get("kind", "done")   # "start" | "done"
    corr = body.get("corr", "")       # correlation id — pairs start+done
    if message or kind == "start":
        entry = log(agent, message or "…", kind, corr)
        # Push live to all WS clients — non-blocking
        asyncio.create_task(manager.broadcast(entry))
    return {"ok": True}


# ============================================================
# FILES — sandboxed to WORKSPACE root (see files.py)
# ============================================================
from files import list_tree, read_file, write_file, make_dir, delete_path


@app.get("/files/tree")
def files_tree(path: str = "", depth: int = 3, user: dict = Depends(require_auth)):
    return list_tree(path, depth)


@app.get("/files/read")
def files_read(path: str, user: dict = Depends(require_auth)):
    return read_file(path)


@app.post("/files/write")
def files_write(body: dict, user: dict = Depends(require_auth)):
    return write_file(body.get("path", ""), body.get("content", ""))


@app.post("/files/mkdir")
def files_mkdir(body: dict, user: dict = Depends(require_auth)):
    return make_dir(body.get("path", ""))


@app.post("/files/delete")
def files_delete(body: dict, user: dict = Depends(require_auth)):
    return delete_path(body.get("path", ""))


# ============================================================
# 3D SCENE GENERATOR — specialized NEO system prompt
# ============================================================
THREEJS_SYSTEM = (
    "You are NEO — a Three.js code generator. "
    "Given a user description, output ONLY valid JavaScript code that renders a scene using Three.js r160. "
    "Rules:\n"
    "1. Do NOT include <script> tags, HTML, markdown fences, or commentary.\n"
    "2. Assume these globals are ALREADY available: THREE, scene, camera, renderer, container.\n"
    "3. You may call `animate(fn)` to register per-frame callback.\n"
    "4. Do NOT create your own renderer/camera/scene — use the provided ones.\n"
    "5. Use bright colors, decent lighting, and ensure the object is visible.\n"
    "6. Keep code under 120 lines.\n"
    "7. Respond in English — code only."
)


@app.post("/gen3d")
@limiter.limit("10/minute")
async def generate_3d(request: Request, body: dict, user: dict = Depends(require_auth)):
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return {"error": "no prompt"}
    client = anthropic.AsyncAnthropic(api_key=anthropic_key())
    api_model = resolve_model(body.get("model", "claude-sonnet-4-6"))

    async def generate():
        try:
            async with client.messages.stream(
                model=api_model,
                max_tokens=2500,
                system=THREEJS_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except BaseException as e:
            import asyncio as _aio
            if isinstance(e, _aio.CancelledError):
                raise
            import traceback, sys
            traceback.print_exc(file=sys.stderr)
            yield f"\n// stream error: {type(e).__name__}: {str(e)[:300]}"

    return StreamingResponse(generate(), media_type="text/plain")


# Serve all .html/.css/.js from project root (must be LAST — catch-all).
# Google OAuth origin (http://localhost:8000) stays the same.
app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent.parent, html=True),
    name="static",
)
