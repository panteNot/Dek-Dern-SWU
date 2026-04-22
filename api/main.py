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
import asyncio, json, os, anthropic
import db

load_dotenv()

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

# Model whitelist — กัน frontend ส่ง model ปลอม
MODELS = {
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
}


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

    # Load prior history (Claude expects alternating user/assistant)
    history = []
    if conv_id:
        existing = db.get_conversation(conv_id)
        if existing:
            history = db.get_history(conv_id)
        else:
            conv_id = None  # invalid id, treat as new

    # Auto-create conversation on first turn (title from first prompt)
    if persist and not conv_id:
        title = prompt[:80].replace("\n", " ").strip() or "New chat"
        conv_id = db.create_conversation(title, agent, model)

    if persist:
        db.append_message(conv_id, "user", prompt, "")

    messages = history + [{"role": "user", "content": prompt}]
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def generate():
        full = ""
        # Send conv_id to frontend in a header-like first line (JSON-prefixed)
        if conv_id:
            yield f"\u0000CONV:{conv_id}\u0000"
        async with client.messages.stream(
            model=model,
            max_tokens=800,  # brief-by-default; long form costs money
            system=AGENTS[agent],
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                full += text
                yield text
        if persist and conv_id and full:
            db.append_message(conv_id, "assistant", full, agent)

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

    async def stream():
        async for event in orchestrate(prompt, AGENTS, agent, model):
            yield json.dumps(event, ensure_ascii=False) + "\n"
            # Also broadcast handoff/done events to activity feed
            t = event.get("type")
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

    return StreamingResponse(stream(), media_type="application/x-ndjson")


# ============================================================
# CONVERSATIONS — SQLite persistence
# ============================================================
@app.get("/conversations")
def conversations_list(user: dict = Depends(require_auth)):
    return db.list_conversations()


@app.get("/conversations/{conv_id}")
def conversations_get(conv_id: str, user: dict = Depends(require_auth)):
    conv = db.get_conversation(conv_id)
    if not conv:
        return {"error": "not found"}
    return conv


@app.delete("/conversations/{conv_id}")
def conversations_delete(conv_id: str, user: dict = Depends(require_auth)):
    ok = db.delete_conversation(conv_id)
    return {"ok": ok}


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
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def generate():
        async with client.messages.stream(
            model=body.get("model", "claude-sonnet-4-6"),
            max_tokens=2500,
            system=THREEJS_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    return StreamingResponse(generate(), media_type="text/plain")


# Serve all .html/.css/.js from project root (must be LAST — catch-all).
# Google OAuth origin (http://localhost:8000) stays the same.
app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent.parent, html=True),
    name="static",
)
