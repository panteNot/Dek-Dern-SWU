"""Claude Code PreToolUse hook — fires the instant the Agent tool is invoked.

Sends `kind: 'start'` to /log so the office page can render a "thinking..."
placeholder + animate the matching pixel robot BEFORE the agent finishes.
"""
import json, os, sys, urllib.request

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

inp = data.get("tool_input", {}) or {}
agent = inp.get("subagent_type", "neo")
if not isinstance(agent, str) or not agent:
    agent = "neo"
agent = agent.lower().strip()

desc = inp.get("description", "กำลังเริ่มทำงาน...")
corr = str(data.get("tool_use_id") or "")[:16]

try:
    req = urllib.request.Request(
        "http://localhost:8000/log",
        data=json.dumps({
            "agent": agent,
            "message": str(desc)[:80],
            "kind": "start",
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
    pass
