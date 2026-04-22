"""Agent activity logger — เขียน log ลง activity.json เพื่อให้ office page อ่านได้"""
import json, sys, os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "activity.json"
MAX_ENTRIES = 50

# สี agent ตรงกับ CSS ใน neo-labs-office.html
AGENT_COLORS = {
    "neo":   "#ff6b00",
    "atlas": "#00c896",
    "nova":  "#a855f7",
    "luna":  "#ec4899",
    "pixel": "#22c55e",
    "sage":  "#eab308",
    "rex":   "#ef4444",
    "byte":  "#3b82f6",
    "quill": "#94a3b8",
}

def log(agent: str, message: str, kind: str = "done", corr: str = "") -> dict:
    """Write an activity entry and return it.

    kind: "start" (agent spun up — show thinking dots)
          "done"  (agent finished — show message; default)
    corr: correlation id — pair start+done so frontend can replace the
          placeholder in-place instead of stacking two entries.
    """
    agent = agent.lower()
    color = AGENT_COLORS.get(agent, "#ffffff")

    entry = {
        "agent": agent.upper(),
        "color": color,
        "message": message,
        "kind": kind,
        "corr": corr,
        "time": datetime.now().strftime("%H:%M:%S"),
        "ts": datetime.now().isoformat(),
    }

    entries = []
    if LOG_FILE.exists():
        try:
            entries = json.loads(LOG_FILE.read_text())
        except Exception:
            entries = []

    # ใหม่อยู่ข้างหน้า, cap ที่ MAX_ENTRIES
    entries.insert(0, entry)
    entries = entries[:MAX_ENTRIES]
    LOG_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2))
    return entry

if __name__ == "__main__":
    # ใช้ตรงๆ: python logger.py neo "กำลังวางแผน..."
    # หรือ:    python logger.py neo "..." start abc123
    if len(sys.argv) >= 3:
        kind = sys.argv[3] if len(sys.argv) >= 4 else "done"
        corr = sys.argv[4] if len(sys.argv) >= 5 else ""
        log(sys.argv[1], sys.argv[2], kind, corr)
    else:
        print("Usage: python logger.py <agent> <message> [kind] [corr]")
