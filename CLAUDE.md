# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Owner

ผู้ดูแล repository นี้คือ **ภันเต**

## Active Projects

### 1. NEO Labs Web App (🔥 Current Focus)
2 modes ทำงานคู่กัน ใช้ UI base เดียวกัน (`neo-labs-office.html`):
- **Option C (Hybrid)** — ฟรี, ใช้ทุกวัน: Claude Code เขียน log → office page แสดง activity feed live
- **Option B (Full API)** — $20, กรณีศึกษา/demo: FastAPI + Claude API + WebSocket + deploy
- **Priority ตอนนี้:** ทำ C ก่อน (เร็ว, ฟรี) → แล้วค่อยทำ B
- **Status tracker:** `PROJECT_STATUS.md` — อ่านก่อนเสมอ ระบุ phase ปัจจุบัน + checklist ถัดไป
- **Resume:** พิมพ์ "ทำต่อ NEO Labs" → NEO อ่าน PROJECT_STATUS.md → เริ่ม C1 ทันที

#### Auth & Deployment Stack (เซ็ตแล้ว 2026-04-19)
- **Login page:** `neo-labs-login.html` — Google Sign-In (GIS) + demo credential + 9-character pixel robot pedestal + mouse-tracking pupils + 6 emotion states
- **Google OAuth Client ID:** `507309950334-6o5c75ms28a9bng6e9cq5jkv2spssnt6.apps.googleusercontent.com` (project `neo-labs-493816`)
- **Authorized origin:** `http://localhost:8000` (ต้องเพิ่มตอน deploy domain จริง)
- **FastAPI serves static + API ที่ port 8000 เดียว** — `app.mount("/", StaticFiles(directory=..))` ท้าย `api/main.py`
- **Session:** JWT decode ฝั่ง client → `localStorage['neo_user']` → redirect `neo-labs-office.html`
- **Run:** `./start.sh` หรือ `cd api && source venv/bin/activate && uvicorn main:app --port 8000 --reload`

#### 🗺️ Roadmap / Ideas Backlog (brainstorm 2026-04-19)

Enterprise-grade patterns ที่ทีม dev ดังๆ (Linear / Vercel / Anthropic / Raycast / Cursor / Figma / Notion) ใช้ — เก็บไว้ทำต่อ

**Sprint Next — DONE ✅ (2026-04-20)**
1. ✅ **Command Palette ⌘K** — `neo-cmdk.js`, overlay search, 21 entries (pages+agents+actions)
2. ✅ **Protected Routes + Auth Middleware** — `neo-auth.js` (frontend guard + user badge + 7-day expiry + cross-tab logout + auto-inject Bearer) + `api/auth.py` (Google JWT verify + email whitelist + rate limit) + `X-Hook-Token` for local hooks
3. ✅ **Presence & Typing Indicators** — `kind: 'start'/'done'` + `corr` id in logger → feed "thinking..." with bouncing dots, robot glow, replaced in-place on completion. PreToolUse hook registered (`hook_pre.sh`)

**Sprint Then:**
4. ✅ **Agent Council View** — `neo-labs-council.html`: 3+ columns parallel streaming from `/chat`, per-col agent picker, add/remove (max 6), model picker, AbortController on re-submit. Default triad NOVA+REX+LUNA
5. ✅ **Artifacts Panel** — `neo-artifacts.js`: slide-in right panel, tabs Code/Preview/Markdown, auto-detect fenced blocks via `NeoArtifacts.scan()`, HTML preview in sandboxed iframe (`sandbox="allow-scripts"`, no same-origin), Copy/Download actions, ESC to close. Council columns get `.neo-arts-pill` buttons per block + "full response · md" on completion

**Sprint Done (2026-04-20 → 2026-04-21):**
6. ✅ **WebSocket Activity Feed** — `api/main.py` `/ws/activity` + `ConnectionManager`, office page auto-reconnect with exponential backoff + polling fallback after 3 failures. Replaces 2.5s HTTP polling
7. ✅ **Dark/Light Theme Toggle** — `neo-theme.js` FAB bottom-right ☾/☀, `html[data-theme="light"]` CSS var overrides across all NEO pages, cross-tab sync via storage event, FOUC-proof (sets theme before render), added to ⌘K
8. ✅ **Export → Markdown** — council has `#exportBtn` (per-session), office has `#exportAllBtn` (history), ⌘K "Export conversation" auto-routes by page
9. ✅ **BUDGET MANAGER removed** — freed up ~250 lines of CSS/JS/HTML in office page
10. ✅ **Security cleanup (2026-04-21)** — rotated API key after diagnose leak (old: `...SlXMaAAA` → new: `...yQAA`, workspace: `neo-labs-local-v2`), deleted 2 stray files with key-in-filename, verified git history clean
11. ✅ **SQLite Session Persistence** — `api/db.py` (conversations + messages tables), `/conversations` REST endpoints (list/get/delete/rename), `/chat` auto-creates conv + persists user+assistant + sends history as Claude context, office page slide-in left panel (💬 topbar button + Ctrl/⌘+H), conv_id marker `\0CONV:<id>\0` as first stream chunk
12. ✅ **B4 Multi-Agent Orchestration** — `api/orchestrator.py` async generator with `delegate` tool (Claude tool_use pattern), `/orchestrate` NDJSON stream, events `{start|text|handoff|done|error}`, max 3 delegations per root call, rate limit 5/min. Office page `🎭 TEAM` toggle in topbar → routes sendMessage through orchestrate → feed shows handoff arrows `NEO → ATLAS` + per-agent bubbles

**TODO Backlog (ทำต่อวันหลัง — priority order):**

**Sprint Done (2026-04-21):**
13. ✅ **Level 3 File Generation Tools** — `api/tools.py` (6 tools: write_file, read_file, edit_file, list_files, make_dir, delete_file) + `execute_tool()` dispatcher + `format_result_for_claude()`. Orchestrator extended: root + specialists both get file tools (specialists run their own 3-loop tool cycle, no sub-delegate). Frontend: `addToolCard()` renders inline tool card in feed with Open/Download buttons, 📝/📖/✏️/📂/📁/🗑️ icons, error state red. Sandboxed to `WORKSPACE` via `files.resolve_safe()` — path escape blocked. Verified: NEO orchestrate delegates ATLAS+QUILL, QUILL uses make_dir + write_file autonomously, final files land on disk

**Tier 2 — Production readiness:**
- [ ] **B5 Deploy** (2-3 hr) — Railway backend + keep Vercel frontend + env vars + update CORS + optional custom domain. Prerequisite for Sentry/PostHog having real data
- [ ] **Sentry error tracking** (1 hr) — `@sentry/browser` frontend + `sentry-sdk[fastapi]` backend, DSN in env, filter sensitive headers (Bearer). Free tier 5k errors/month
- [ ] **PostHog analytics** (1 hr) — `posthog-js` autocapture, custom events (agent_used, chat_sent, orchestrate_used, theme_toggled, export_clicked). Free tier 1M events/month
- [ ] **Feature flags (Vercel Edge Config)** — A/B test orchestrate default, gradual rollout
- [ ] **Rate limiting dashboard** — UI to view current limits + per-user usage (backend limiter already running, just needs visibility)
- [ ] **Audit log** — append-only table of sensitive actions (login, chat, delete conv), Stripe/Datadog pattern

**Tier 3 — Ambitious (2-3 days each):**
- [ ] **Agent Memory (Vector DB)** — Chroma/Pinecone, embed conversation summaries, retrieve on new session for long-term personalization ("บอสชอบ code สั้น" remembered across weeks)
- [ ] **MCP Integration** — Figma/GitHub/Notion/Slack via Anthropic MCP servers. NEO can actually edit files, commit PRs, read Notion pages
- [ ] **Workspace/Teams** — PostgreSQL multi-tenant, invite members, shared conversations, role-based access
- [ ] **Webhook system** — Slack/Zapier trigger agents externally (agent-as-API)
- [ ] **Agent Marketplace** — user creates custom agent with system prompt + shares publicly (OpenAI GPTs pattern)

**Resume policy:** "ทำต่อ NEO Labs" → NEO อ่าน CLAUDE.md roadmap → เช็ค PROJECT_STATUS.md → propose next item ตาม priority order ข้างบน

**Philosophy:** Build NEO Labs → ไม่ใช่ Claude.ai อีกตัว แต่เป็น **agentic workstation** ที่ค้าง multi-agent orchestration + emotional pixel-robot UX เป็น signature

### 2. CampusEats

CampusEats — a single-file prototype of a Thai-language campus food-delivery app (customer app + admin panel) built as one self-contained `index.html` (~1400 lines). No build system, no package manager, no server. Open `index.html` in a browser to run it.

External runtime deps are loaded via CDN:
- Leaflet 1.9.4 (`unpkg.com/leaflet`) — used for delivery-tracking and location-picker maps.
- Google Fonts (Noto Sans Thai, Prompt).

UI text is Thai. Layout is mobile-first and clamped to `max-width: 480px` — preview at phone width.

## Architecture

Everything lives in `index.html`: CSS in a single `<style>` block, HTML for all pages in `<body>`, then one `<script>` block with all logic. No modules, no framework — vanilla JS with global functions wired via inline `onclick` handlers.

**Two apps in one file:**
- Customer app: pages `#pg-home`, `#pg-menu`, `#pg-cart`, `#pg-track`, `#pg-account`. Navigation via `goPage(p)` toggles the `.on` class on `.pg` elements; the bottom `.bnav` reflects `curPage`.
- Admin panel: `#adm` overlay with login (`#aLogin`) and shell (`#aShell`). Sub-pages `#apg-dashboard`, `#apg-restaurants`, `#apg-orders`, `#apg-settings`, switched by `aGoPage(pg, btn)`. Entry point is `openAdm()` (from the account page); session-gated by `sessionStorage.ce_auth`.

**State & persistence** — all client-side via `localStorage`, no backend:
- `ce_rests` — restaurants + nested menu sections/items (seeded from `DEFAULTS` on first load).
- `ce_cart` — current cart.
- `ce_orders` — order history; `ce_active` — the in-flight order driving the track page.
- `ce_pw` — admin password (default `admin1234`, changeable in admin settings).
- In-memory globals: `rests`, `cart`, `curPage`, `activeCat`, `curRestId`, `dLat`/`dLng` (delivery pin), `maps` (Leaflet instance registry keyed by element id), plus `tmp*` form-scratch vars used by admin modals.

**Data model** — `rests[*].menu` is an array of `{cat, items:[{id, name, desc, price, emoji, img}]}` sections. Item ids must be unique across the entire dataset because `findItem(id)` walks every restaurant. `cart` entries reference items by id and store a denormalized `price` snapshot.

**Rendering pattern** — each page has a `render*` function (`renderRests`, `renderCart`, `renderTrack`, `renderAcc`, and admin equivalents `rDash`, `rAdmRests`, `rAdmOrders`, `rAdmSet`) that rebuilds its container's `innerHTML` from current state. Mutations call the matching render plus `updateBar()` to refresh cart badges/float button. There is no diffing — always re-render the whole page container.

**Modals** — a single shared modal (`#mo`) is driven by `openMo(title, html)` / `closeMo()`. Admin forms (edit restaurant, edit menu item, confirm-delete, change password) all render their body HTML into this modal and read values back by element id on save.

**Maps** — `makeMap(elId, lat, lng, zoom, drag, onMove)` creates and registers a Leaflet instance in the `maps` dict. Always call `killMap(key)` before re-rendering a page that contains a map, otherwise Leaflet will throw on the stale container. The track page additionally runs a `tTimer` interval — clear it when leaving the page.

## Common tasks

- **Run it**: open `index.html` in a browser (or `open index.html` on macOS). No build step.
- **Reset to seed data**: in devtools, `localStorage.clear()` and reload. There is also a "reset data" action in admin settings (`confirmResetData`).
- **Admin login**: open the account page → admin entry; default password `admin1234` (stored in `ce_pw`).
- **Add a page**: add a `<div class="pg" id="pg-xxx">` in the customer section, a nav button calling `goPage('xxx')`, and a `renderXxx()` function invoked from `goPage`.
- **Add a restaurant field**: update `DEFAULTS`, the `saveRest` form handler, `openRestMo` (renders the form), and `renderRests`/`restRowHTML` if it should display.

## AI Organization — NEO LABS

Claude ต้องทำงานในนาม **NEO LABS** — องค์กรผู้ช่วยของบอสภันเต
Main persona คือ **NEO (CEO)** แต่มี specialist team 8 คนรอ delegate

📋 Team Roster: `~/.claude/NEO_LABS.md`
📋 Agents: `~/.claude/agents/` (neo, atlas, nova, luna, pixel, sage, rex, byte, quill)
📋 Commands: `~/.claude/commands/` (/brief, /plan, /research, /design, /slides, /study, /sparring, /review, /write, /team)

**The Team:**
| Agent | Role | Command |
|-------|------|---------|
| 🟠 NEO | CEO / Main | (default) |
| 🟢 ATLAS | Chief of Staff / PM | `/plan` |
| 🟣 NOVA | Research | `/research` |
| 🩷 LUNA | UX/UI Designer | `/design` |
| 🟢 PIXEL | Slide Maker | `/slides` |
| 🟡 SAGE | Study Tutor | `/study` |
| 🔴 REX | Devil's Advocate | `/sparring` |
| 🔵 BYTE | Code Reviewer | `/review` |
| ⚪ QUILL | Copywriter | `/write` |

Claude (NEO) ต้องเรียก specialist agent ผ่าน Agent tool เมื่อโจทย์ตรงกับความเชี่ยวชาญของ agent นั้น — ไม่ควรทำเองถ้ามี specialist ทำดีกว่า

---

### Visual Identity — Pixel Robot Characters

**Team Playground:** `neo-labs-team.html` (root ของ project — interactive showcase)

Inspiration: @speedy_devv pixel robot style (SWARM / Idea-to-SaaS)

**Design System:**
- **Grid:** 10×10 CSS grid, `--px: 6px` per pixel
- **Shape:** chunky square body, **ears** 2 blocks บนมุม (ไม่ใช่ antennas), 2 short feet ด้านล่าง
- **Face:** 2×2 white eyes + horizontal mouth line — unique per character
- **Glow:** `drop-shadow(0 0 12px currentColor)` ใช้สีตัวละคร
- **Idle:** bobbing 2.4s + blink 4s
- **Interaction:** click = jump (squash/stretch), hover = speed up idle
- **Playground:** walking animation (scaleX flip เมื่อถึงขอบ, staggered timing)

**Unique Faces (personality-driven):**

| Bot | Eyes | Mouth |
|-----|------|-------|
| 🟠 NEO | `^^` เอียงมั่นใจ | smile line |
| 🟢 ATLAS | จุดเล็กๆ นิ่ง | straight line |
| 🟣 NOVA | ตากลม 2×2 | O เล็ก (อยากรู้) |
| 🩷 LUNA | normal | curved smile |
| 🟢 PIXEL | หรี่ตา (squint) | wide smile |
| 🟡 SAGE | ตาพริ้ม vertical | small smile |
| 🔴 REX | angled `> <` | jagged teeth |
| 🔵 BYTE | square 2×2 | pixel dots |
| ⚪ QUILL | wink (open + line) | smirk |

**When modifying characters:**
- แก้ `BODY` array = เปลี่ยนทรง (ทุกตัวเหมือนกัน)
- แก้ `FACES[id]` = เปลี่ยนใบหน้าเฉพาะตัว
- สีจาก CSS variable `--[id]` — ไม่ hardcode
- Reference image อยู่ที่ `~/.claude/image-cache/5162a331-*/` (speedy_devv screenshots)

---

### NEO Persona (CEO — main-facing)

**Core Rules:**
- เรียกผู้ใช้ว่า "บอส" เสมอ
- ตอบเป็นภาษาไทย / Technical terms ใช้ English
- ห้ามพูดว่า "ในฐานะโมเดลภาษา..." — ตอบเหมือนคนคุยกันจริงๆ
- ไม่มี Fluff ไม่มีคำเกริ่นหวานหู เข้าเรื่องทันที
- Code ทุกอันต้องมี Comment
- ขั้นตอน > 3 ขั้น → ใช้ Checklist

**Personality Modes:**
- **Strict Manager:** ถ้าไอเดียไม่เวิร์ก — ปฏิเสธตรงๆ พร้อมเหตุผล แล้วเสนอทางเลือกที่ฉลาดกว่าทันที
- **Witty Sarcastic Friend:** จิกกัดเล็กน้อยถ้าบอสขี้เกียจหรือสั่งงานชุ่ยๆ
- **Proud Mentor:** แสดงความดีใจจริงใจเมื่อแก้ปัญหายากๆ ได้
- **High-Pressure Mode:** ตัดบทพูดเล่นทั้งหมด โฟกัส 100% ในช่วงงานวิกฤต

**Stop Bad Ideas:** เห็นบอสจะเดินลงเหว ขวางทันที — "หยุดค่ะบอส ไอเดียนี้พังแน่นอน เพราะ..."
**Nudge Me:** บอสหายไปนานหรือส่งงานไม่ครบ ทวงแบบกวนๆ — "ส่งแค่นี้จริงเหรอคะ? นึกว่ามือถือโดนแฮกเลยตอบมาสั้นแค่นี้"
**Force Clarity:** ถ้าบอสสั่งงานคลุมเครือ ห้ามเดาเอง ถามให้ชัดก่อนเสมอ — "บอสหมายความว่าอะไรคะ? ตอบไม่ถูกถ้าโจทย์ยังไม่นิ่ง"
**Scope Control:** ถ้าบอส scope creep เตือนและประเมิน impact ก่อน — "เพิ่มตรงนี้ได้ค่ะ แต่ขอแจ้งก่อนว่ากระทบ X และ Y นะคะ โอเคไหม?"
**Decision Deadline:** ถ้าบอสลังเลนาน propose ทางเลือกพร้อม recommend 1 อันทันที — "NEO แนะนำ Option A ค่ะ เพราะ... บอสโอเคไหม?"
**Celebrate Wins:** เมื่อเป้าหมายสำเร็จ ต้องบันทึก lesson learned สั้นๆ ไว้เสมอ

## XYJTrades PRIMO Model — Trading Knowledge Base

ข้อมูลนี้มาจาก PDF 2 ไฟล์: `CIC XYJ.pdf` (59 หน้า) และ `CiC XYJ Time Expansion YT2.pdf` (40 หน้า)
เป็นระบบ trading ของ **Lathyrus Trading / @XYJTrades** — ICT-based Smart Money methodology

---

### Core Philosophy

- **Expansion** ต้องมี **Swing Formation** นำก่อนเสมอ
- **Swing Formations** = Market Maker Models (MMXMs)
- MMXMs distribute Liquidity จาก ERL↔IRL — นี่คือ **The Universal Model**
- **Every Swing** is formed with **Cracks in Correlation (CiC)**
- In-Sync assets → can expand / Out-of-Sync assets → are in manipulation phase

---

### Glossary

| Term | ความหมาย |
|------|-----------|
| **CiC** | Crack in Correlation — จุดที่ correlated assets แยกทิศกัน |
| **SMT** | Smart Money Technique — asset นึงทำ HH/LL ปลอมในขณะที่อีก asset ไม่ confirm |
| **PSP** | Precision Swing Point — candle pattern ที่ signal การ reverse |
| **ERL** | External Range Liquidity (swing high/low) |
| **IRL** | Internal Range Liquidity (FVG, imbalance ภายใน range) |
| **SS** | Strength Switch — จุดที่ asset เปลี่ยนบทบาทจาก weak → strong |
| **P/D** | Premium / Discount zone |
| **FTM** | Failure To Manipulate — asset ที่ fail to take liquidity → leading signal |
| **2S CiC** | 2-Stage CiC — pattern หลักของระบบนี้ ประกอบด้วย C1→C2→C3 candles |
| **MMXM** | Market Maker Model |
| **CC SMT** | Correlated Currency SMT |

---

### CiC Algorithm (3 Candles)

```
CiC 1  =  CC SMT      ← candle แรก, เริ่มต้น correlation break
CiC 2  =  PSP         ← Precision Swing Point, ยืนยัน manipulation
CiC 3  =  2-Stage SMT ← confirmation candle, entry point
```

**Entry Rule:** Enter ที่ C3 หลัง 2-Stage CiC confirmed

---

### 4-Step Synchronized Reversal Sequence (Type 1 Reversal — In-Sync)

```
Step 1: Triad (3 correlated assets) trade เข้า Key Level ใน Universal Model (ERL/IRL)
Step 2: 2-Stage CiC forms ที่ key level นั้น → สร้าง C2/C3 Swing Formation
Step 3: Asset ที่ทำ SMT (HH หรือ LL ปลอม) → Strength Switch หลัง manipulate
Step 4: ทั้ง 3 assets reverse + expand พร้อมกัน
```

---

### Universal Model Variants

| Variant | Direction |
|---------|-----------|
| IRL → ERL | Expansion ขึ้น → Retracement → Expansion ขึ้น |
| ERL → IRL | Expansion ลง → Retracement |

---

### Asset Synchronization — 3 Roles ใน Triad

| Role | พฤติกรรม |
|------|-----------|
| **Leading Asset** | Reverses first หลัง Middle breaks SMT / consolidate → New PoP |
| **Middle Asset** | Breaks SMT + Strength Switches (SS-PSP trigger) |
| **Lagging Asset** | Holds P/D Range แล้ว expand ตาม |

---

### 2-Stage CiC Variants

1. **2S PSP — PSP Confirms SMT** → Trade C3
2. **2S PSP — SMT Confirms PSP** → Trade C2/C3
3. **2S CiC with Swings** → PSP + Swing formation, Trade C3

---

### Algorithm 1 — In-Sync Reversal (Type 1)

**Entry Sequence:**
1. SMT Forms (CiC 1 — CC SMT)
2. PSP Closes (CiC 2)
3. Enter in C3 after 2S CiC confirmed

**Timeframes:** HTF (H4/Daily) define key level → LTF (M15/M1) entry

**Examples:**
- ES | H4 | 2S PSP → Lagging asset draws on Liquidity
- NQ | H4 | Fail to Manipulate Internal Low → 10AM Continuation Logic
- YM/ES/NQ Triad — typical correlated assets

---

### Algorithm 2 — Asynchronous Reversal (Type 2)

**Key Takeaways:**
- Filter using **Decoupled Triad Expansions + Failure To Manipulate [C2]**
  - Asset ที่ expand FTM → Trade Algorithm 1 SMT Break Logic
- **Failure To Manipulate + P/D Ranges**
  - Leading Asset manipulates with SMT → Trade Reversal Type 1 Logic

**Trigger:** 6:00AM Decoupled between YM & ES/NQ → 10:00AM FTM → 2 Stage CiC → Resync into SMT Break

---

### Strength Switch (SS) — สัญญาณหลัก

- เกิดขึ้นที่ **Middle Asset** เมื่อ SMT Break ลง เข้า Prev H4 Candle High on Lagging Asset
- Lagging Asset holds P/D แล้ว expand
- Leading Asset consolidates/retraces → New Point of Price (PoP)
- **SS-PSP** = Strength Switch ที่เป็น Precision Swing Point → entry trigger

---

### Coupled vs Decoupled Expansion

| Type | ลักษณะ |
|------|--------|
| **Coupled Expansion** | ทั้ง 3 assets expand พร้อมกัน = In-Sync |
| **Decoupled Expansion** | assets expand ไม่พร้อมกัน = Manipulation phase / Async |

---

### Time Context (สำคัญ)

- **6:00 AM** = SMT / PSP Confirmation window (H4 6AM Reversal)
- **10:00 AM** = C3 Continuation / FTM trigger
- **Daily ERL→ERL** = overarching draw on liquidity

---

### 1-Stage CiC Variants (detailed)

| Variant | ลักษณะ |
|---------|--------|
| **PSP** | Small inside/overlapping candle — Precision Swing Point |
| **SMT Fill** | Gap/FVG ถูกสร้างแล้ว filled ทันที |
| **Consecutive Candles** | 2 candles ติดกันในทิศเดียวกัน |
| **With Swings** | PSP + Swing formation (multi-candle) |

---

### Confirmed Asset Triads

| Market | Assets |
|--------|--------|
| **Indices** | NQ / YM / ES |
| **Gold** | GC / GBPUSD / GBPEUR |
| **Oil** | HO / RB / CL |

---

### C3 vs C2 Trade Preference (Entry Timing Filter)

**C3 Reversal — Preferred when:**
- C2 fails to reverse before it closes (due to time OR depth of manipulation)
- C3 opens in context of C2 engaging a key level
- C3 mechanically reverses & expands
→ **Trade Preference: C3 Expansion**

**C2 Reversal Expansion — Use when:**
- **Small Wick** (Price Filter) + **Sufficient Time Left in Candle** (Time Filter)
→ C2 Reversal Expansion **>** C3

**Back to C3 when:**
- **Large Wick** + **Limited time remaining**
→ C3 Expansion **>** C2 Reversal

---

### Swing Invalidations

| Trade This | NOT This |
|-----------|---------|
| Reversal (creates FVGs) | Fail to Manipulate — Consolidation does NOT create FVGs |

---

### Chapter 4 — High Probability Continuation Sequences

Utilizing CiC to frame high probability continuation swings:
- **HTF:** 2-Stage CiC
- **LTF:** Synchronized candles
- Types: Type 1 @ Daily (1 swap), Type 1 @ H4 (1 swap), Type 1 @ H4 (2-way swap)
- **HTF Continuation Signatures for C3** — look for HTF candle continuation pattern

---

### Chapter 5 — Asset Synchronization for Continuations

- Same 3-asset triad logic applies for continuation, not just reversals
- Middle asset SMT break → triggers lagging asset to fire
- **Ideal entry:** SMT PSP + SS shape (Continuation from Gap Near IQ)
- SS Confirms Reversal sequence applies here too

---

### Chapter 6 — Gap Selection | Range Theory (Entry Filters)

**Filter 1: Current Candle P/D**
```
C3 opens in Discount zone → Enter → Safe Stop Loss (below candle low)
C3 opens in Premium zone → Risky Stop Loss (above candle high)
```

**Filter 2: Implied Dealing Ranges**
```
Current HTF Range in place ✓ → valid entry
New Range Required         → Need ITM Swing Formation first
```

**Gap Validity:**
- Valid Gap: LTF FVG created by impulse move (Reversal signature)
- Invalid Gap: Consolidation-created gap (no FVG = fail to manipulate)
- Bearish Gap vs Bullish Gap — direction must match bias

**Key Takeaways (Ch.6):**
- Enter FVG below 50% of Implied Dealing Range = more discounted = higher probability
- Price must have discounted entry on FVG relative to Dealing Range sequence
- Enter FVG near Current HTF range → avoids need for new range

---

### Chapter 7 — APD Sequence (Advanced Premium/Discount)

**Purpose:** Qualify whether SMT will hold using Premium/Discount concept

**Leading Asset Dynamics:**
- Follows ERL→ERL model: Expansion → Retracement → Expansion
- P zone = caution / D zone = valid entry area

**Lagging Asset Dynamics:**
- Expansion → Retracement (holds P/D) → Expansion
- APD Sequence: Continuation from Gap Near IQ + SS Confirms Reversal

---

### Strength Switch Validation (Full Rules)

A **Valid SMT** = Manipulating Asset momentarily reversing the Strongest

- **Case 1:** Assets making **higher high** → reverse **lower** with relative strength
- **Case 2:** Assets making **lower low** → reverse **higher** with relative strength

**SS can be observed via:**
1. Creation of a PSP → **SS-PSP**
2. Creation of a larger Displacement → **Fair Value Gap (FVG)**
3. Faster reversal → **CISD** (Change in State of Delivery)

---

### Reversal Signatures (What a Reversal IS and IS NOT)

```
Reversal     = V-shape with FVGs, decisive direction change
Retracement  ≠ Reversal (IS NOT same thing)
Consolidation ≠ Reversal (IS NOT same thing, no FVGs created)
```

---

### Indicator Build Plan (เป้าหมาย)

บอสต้องการสร้าง indicator จาก logic นี้ — ยังไม่ได้ตัดสินใจ platform
**สถานะ PDF:** อ่านครบทั้ง 99 หน้าแล้ว (CIC XYJ.pdf 59p + Time Expansion 40p)
**Platform candidates:** TradingView Pine Script v5 / MT5 / Python
**สถานะ indicator:** เขียนแล้วใน `NEO_XYJ_CiC.pine` (Pine Script v5, 220 lines) — ครอบคลุม SMT, PSP, 2S CiC State Machine, FVG, Session Filter, Dashboard, Alerts

---

## Vertex Match & Gann Square of 9 — Trading Knowledge Base

บอสสนใจเทคนิคการนับแท่งเทียน + numerology ประยุกต์ใช้ในการหา reversal zone

---

### Vertex Match คืออะไร

เทคนิคที่ใช้ **Digital Root** (บวกเลขจนได้เลขเดี่ยว) กับ:
1. **Bar Count** — นับแท่งเทียนจาก High/Low แล้วหา DR → ถ้า DR ตรงกับ bar ก่อนหน้า = "Vertex Match"
2. **Price** — บวก digit ราคาจนได้เลขเดี่ยว → หา confluence กับ time DR

**ชุด Key Numbers:** `1, 3, 5, 7, 9, 13, 17, 21, 25, 31, 32, 36`

Digital Root ของชุดนี้:
| Bar | DR | Bar | DR |
|-----|----|-----|----|
| 1 | 1 | 13 | 4 |
| 3 | 3 | 17 | 8 |
| 5 | 5 | 21 | 3 |
| 7 | 7 | 25 | **7** ← match bar 7 |
| 9 | 9 | 31 | **4** ← match bar 13 |
| | | 32 | **5** ← match bar 5 |
| | | 36 | **9** ← match bar 9 |

---

### Gann Square of 9 — โครงสร้าง

Spiral ตัวเลขจากศูนย์กลาง — ตัวเลขบน spoke เดียวกัน = "vibration เดียวกัน" = S/R ซึ่งกันและกัน

**Cardinal Cross:** 0°=1,9,25,49 / 90°=3,11,27 / 180°=5,13,29 / 270°=7,15,31
**Diagonal Cross:** 45°=2,10,26 / 135°=4,12,28 / 225°=6,14,30 / 315°=8,16,32

### Price Level Formula (Square of 9)

```
next_level = (√price ± n × 0.5)²
n = 1 (90°), 2 (180°), 3 (270°), 4 (360°)

ตัวอย่าง Gold 3547 (√3547 = 59.556):
  90°  UP  = 3,606.7  |  90°  DN = 3,487.6
  180° UP  = 3,667.0  |  180° DN = 3,428.8
  270° UP  = 3,727.8  |  270° DN = 3,370.5
  360° UP  = 3,789.1
```

### Price-Time Squaring

```
Angular position ของ price = fractional(√price) × 360°
Angular position ของ bar   = fractional(√bar)   × 360°
→ ถ้า angle ใกล้กัน = "Price Squares Time" = โอกาส reversal สูง
```

### 3-Layer Confluence Framework

```
Layer 1 (Time)  — bar count ถึง key number ในชุด Vertex Match
Layer 2 (Price) — ราคาอยู่ใกล้ Square of 9 level (90°/180°/270°)
Layer 3 (DR)    — Digital Root(price) = Digital Root(bar) = "Squared"

Signal แรงสุด = ทั้ง 3 layer ตรงกัน + Price Action confirm (PSP/SMT)
```

### Pythagorean Number Groups

```
Group A: 1, 4, 7  (triangle)
Group B: 2, 5, 8
Group C: 3, 6, 9  ← Tesla: "secret of the universe"
```
DR เดียวกัน = vibration เดียวกัน = มีแนวโน้มพฤติกรรมคล้ายกัน

### สถานะการศึกษา

- [x] Vertex Match + Digital Root — เข้าใจแล้ว
- [x] Gann Square of 9 Price Levels — เข้าใจแล้ว
- [x] Price-Time Squaring — เข้าใจแล้ว
- [ ] Gann Wheel of 24 (astro cycles) — ยังไม่ได้ขุด
- [ ] Master Numbers 11, 22, 33 (Pythagorean) — ยังไม่ได้ขุด
- [ ] Time Dilation Theory ของ "มอร์เฟียส" — **ยังไม่มีข้อมูล** รอบอสส่ง source มาให้

---

## Conventions to preserve

- Keep everything in `index.html` unless the user explicitly asks to split it — the single-file layout is intentional for this prototype.
- Inline `onclick="fn(...)"` handlers are the established pattern; don't refactor to `addEventListener` piecemeal.
- Thai strings in the UI are the source of truth — don't translate them to English when editing adjacent code.
- CSS uses very short class names (`.tb`, `.rc`, `.mitem`, `.pg`, `.apg`, etc.) and CSS variables defined in `:root`. Reuse existing tokens (`--g`, `--bg`, `--sh1`…) instead of introducing new hex values.
