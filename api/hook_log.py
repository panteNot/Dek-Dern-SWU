"""Claude Code PostToolUse hook — parse Agent tool call → ส่งไป /log"""
import json, sys, re, urllib.request

# อ่าน JSON จาก stdin (Claude Code pipe เข้ามา)
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

inp = data.get("tool_input", {}) or {}
out = data.get("tool_response", data.get("tool_output", {})) or {}

# 1) agent name จาก subagent_type
agent = inp.get("subagent_type", "neo")
if not isinstance(agent, str) or not agent:
    agent = "neo"
agent = agent.lower().strip()

# 2) ดึงคำตอบจริงจาก tool_output
message = ""
if isinstance(out, dict):
    content = out.get("content", out.get("result", ""))
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                message = c.get("text", "")
                break
    elif isinstance(content, str):
        message = content
elif isinstance(out, str):
    message = out

# 3) Clean — เอาเฉพาะบรรทัดแรกที่มีความหมาย
if message:
    # ตัด signature ท้าย ("— NOVA 🟣")
    message = re.split(r"—\s*(NEO|ATLAS|NOVA|LUNA|PIXEL|SAGE|REX|BYTE|QUILL)", message)[0]
    # ตัด metadata (agentId, usage tag)
    message = re.split(r"agentId:|<usage>", message)[0]

    # หาบรรทัดแรกที่ไม่ใช่ header / separator
    lines = [l.strip() for l in message.split("\n") if l.strip()]
    lines = [l for l in lines if not l.startswith("#") and not l.startswith("---")]
    message = lines[0] if lines else ""

# 4) Fallback — ใช้ description ถ้ายังไม่มี
if not message:
    message = inp.get("description", "กำลังทำงาน...")

message = str(message)[:120]

# correlation id — pair with the matching PreToolUse entry (if it fired)
corr = str(data.get("tool_use_id") or "")[:16]

# ส่งไป FastAPI — ต้องใส่ X-Hook-Token เพราะ /log ถูก protect
try:
    import os
    req = urllib.request.Request(
        "http://localhost:8000/log",
        data=json.dumps({
            "agent": agent,
            "message": message,
            "kind": "done",
            "corr": corr,
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Hook-Token": os.environ.get("NEO_HOOK_TOKEN", "local-hook-dev-only"),
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=2)
except Exception:
    pass  # server ไม่ได้รัน — ข้ามไป
