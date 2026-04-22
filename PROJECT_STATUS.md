# NEO Labs Web App — Project Status

> **Vision:** 2 modes ทำงานคู่กัน — C ใช้ทุกวัน, B ใช้กรณีศึกษา/demo
> UI base เดียวกัน: `neo-labs-office.html` + Activity Feed

---

## แผน 2 Mode

| | **Option C (Hybrid)** | **Option B (Full API)** |
|---|---|---|
| **ใช้เมื่อ** | ทุกวัน | กรณีศึกษา / demo / โชว์คนอื่น |
| **Agent คิดที่ไหน** | Claude Code (Terminal) | Claude API (backend) |
| **เปิดจาก** | Browser local file | Browser จาก URL |
| **ราคา** | ฟรี | $20 credit |
| **Deploy** | ไม่ต้อง | Railway + Vercel |
| **UI** | `neo-labs-office.html` | `neo-labs-office.html` (เดิม) |

**ลำดับ:** ทำ C ก่อน → ใช้ได้ทันที → ค่อยทำ B ต่อยอด

---

## Stack

- **Backend (B only):** Python + FastAPI
- **AI (B only):** Claude API (`claude-opus-4-7` specialists, `claude-haiku` routing)
- **Real-time (B only):** WebSocket (streaming)
- **Frontend (ทั้ง B+C):** `neo-labs-office.html` + `neo-labs-team.html`
- **Agents:** 9 คน จาก `~/.claude/agents/`
- **Deploy (B only):** Railway / Render (backend) + Vercel (frontend)

---

## Phase Progress — Option C (Hybrid) ✅ เสร็จทั้งหมด

| Phase | Task | Effort | Status |
|-------|------|--------|--------|
| C1 | logger.py + activity.json + /log, /activity endpoints | 2-3 hr | ✅ Done (2026-04-17) |
| C2 | HTML polling + Claude Code hook → real agent response in feed | 2-3 hr | ✅ Done (2026-04-17) |
| C3 | Robot speak + bubble + feed animation (ผ่าน speak() เดิม) | 1-2 hr | ✅ Done (2026-04-17) |

**Total C:** เสร็จแล้ว (ใช้ได้ทุกวัน, ฟรี)

---

## Phase Progress — Option B (Full API)

| Phase | Task | Effort | Status |
|-------|------|--------|--------|
| B1 | Backend Foundation (FastAPI skeleton + Claude SDK + env) | 3-4 hr | ✅ Done (2026-04-17) |
| B2 | Single Agent Call (NEO only, HTTP) | 2-3 hr | ⏳ Blocked (ต้องการ API key จริง) |
| B3 | WebSocket + Live Feed (streaming) | 3-4 hr | ⏳ Not started |
| B4 | Multi-Agent Orchestration (9 agents + handoff) | 6-8 hr | ⏳ Not started |
| B5 | Polish + Deploy | 1-2 hr | ⏳ Not started |

**Total B:** 15-21 hr (~3-5 วัน, $20)

---

## Current Position

**✅ Option C เสร็จสมบูรณ์ — ใช้ได้ทุกวันแล้ว**
**⏳ Option B รอบอสตัดสินใจว่าจะทำไหม (ต้อง API key $20)**

สิ่งที่ทำไปแล้ว (B1 + C1 + C2 + C3):
- [x] `api/main.py` — FastAPI + CORS + `/health`, `/log`, `/activity`
- [x] `api/logger.py` — เขียน activity.json + 9 agent colors
- [x] `api/hook_log.py` + `hook_log.sh` — parse tool_response → ส่ง real message
- [x] `~/.claude/settings.json` — PostToolUse hook บน Agent tool
- [x] `neo-labs-office.html` — poll `/activity` ทุก 2 วินาที → speak()
- [x] venv + dependencies ติดตั้งครบ
- [x] Tested: เรียก REX/QUILL/NOVA → เห็น real response ใน feed

**วิธีใช้ C mode (ทุกวัน):**
1. Terminal: `cd api && source venv/bin/activate && uvicorn main:app --port 8000`
2. Browser: เปิด `neo-labs-office.html`
3. คุยกับ NEO ใน Claude Code ตามปกติ → เห็น robot เคลื่อนไหว + feed live

⚠️ B2+ blocked: ต้องมี ANTHROPIC_API_KEY จริงก่อน (console.anthropic.com)

---

## Option C — Next Checklist (เริ่มครั้งต่อไป)

- [ ] สร้าง `api/logger.py` — เขียน agent activity log ลง `api/activity.json`
- [ ] Hook Claude Code ให้ส่ง log ทุกครั้งที่ agent ถูกเรียก
- [ ] แก้ `neo-labs-office.html` ให้ poll `activity.json` ทุก 2 วินาที
- [ ] Update Activity Feed + robot animation เมื่อ log เปลี่ยน
- [ ] ทดสอบ: พิมพ์ `/plan` ใน Claude Code → เห็น ATLAS กระโดด

---

## Key Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Agent loop infinite (B) | High | depth limit = 3 hops |
| WebSocket drop เงียบ (B) | Med | auto-reconnect handler |
| Claude API cost (B) | Med | Haiku routing, Opus specialist |
| Log file race condition (C) | Low | append-only JSON + timestamp |

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-17 | Python FastAPI > Node.js | บอสไม่เคย setup backend มาก่อน |
| 2026-04-17 | `neo-labs-office.html` เป็น base UI | สวยอยู่แล้ว + Activity Feed UI ครบ |
| 2026-04-17 | Autonomous mode | บอสต้องการสั่งครั้งเดียว ไม่ micromanage |
| 2026-04-17 | ทำ C+B คู่กัน | C ใช้ทุกวัน (ฟรี), B ใช้กรณีศึกษา ($20) |
| 2026-04-17 | ทำ C ก่อน B | C เร็วกว่า ใช้ได้ก่อน B ไม่ต้องรอ API key |

---

## How to Resume

1. เปิด Claude Code ใน `/Users/akkarawin/Desktop/NewClaude`
2. พิมพ์: **"ทำต่อ NEO Labs"**
3. NEO อ่านไฟล์นี้ → รู้ว่าอยู่ไหน → เริ่ม C1 ต่อได้เลย

---

*Last updated: 2026-04-17 by NEO*
