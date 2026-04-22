"""Multi-agent orchestration — root agent delegates to specialists via 'delegate' tool.

Flow:
  root agent (NEO by default) receives prompt
    → Claude decides to emit tool_use 'delegate' blocks
    → server calls each specialist with their task
    → specialist responses feed back as tool_results
    → root synthesizes final answer
Events are yielded as dicts so the endpoint can serialize them (NDJSON).

Depth limit is enforced by `max_delegations` — flat fan-out, no recursive sub-delegation,
which keeps cost bounded and traces readable.
"""
from __future__ import annotations
import os
import anthropic
from tools import AGENT_TOOLS, TOOL_NAMES, execute_tool, format_result_for_claude


def build_delegate_tool(agent_ids: list[str]) -> dict:
    return {
        "name": "delegate",
        "description": (
            "Delegate a self-contained subtask to a specialist agent whose expertise "
            "fits the subtask better than yours. Use sparingly — only when another "
            "agent will clearly do it better. Provide the task in clear, direct Thai."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": agent_ids,
                    "description": "Target specialist agent id (lowercase).",
                },
                "task": {
                    "type": "string",
                    "description": "Clear, self-contained subtask for the specialist. Thai.",
                },
            },
            "required": ["agent", "task"],
        },
    }


ORCHESTRATOR_SUFFIX = (
    "\n\n---\n"
    "**Delegation:** คุณสามารถ delegate งานย่อยให้ specialist agents ผ่าน tool 'delegate' ได้ "
    "ใช้เมื่อเห็นว่าเรื่องนั้น agent อื่นถนัดกว่า (เช่น research → NOVA, design → LUNA, "
    "copy → QUILL, code review → BYTE, stress-test ไอเดีย → REX, plan → ATLAS, "
    "slide → PIXEL, study/explain → SAGE). "
    "หลังได้ผลจาก specialists แล้ว — สรุป + สังเคราะห์ให้บอสเป็นคำตอบเดียว "
    "อย่าก๊อป output ของ specialist มาโต้งๆ"
    "\n\n**File Tools:** คุณมี tool สำหรับสร้าง/อ่าน/แก้ไขไฟล์ในบอส workspace ด้วย — "
    "ใช้ write_file เมื่อบอสขอให้สร้าง/save ไฟล์ (markdown, code, json, etc). "
    "ใช้ read_file ก่อน edit_file เพื่อดูของเดิม. ใช้ list_files ดู structure. "
    "Path ใช้ relative เช่น 'projects/launch/plan.md'. "
    "เขียนไฟล์เสร็จแล้วให้บอสเปิดดูใน Files tab ได้เลย"
    "\n\n**💰 Cost Control (งบ $20) — Internal Triage:**\n"
    "- **ขั้น 1:** NEO ลองตอบเองก่อนเสมอ. ถ้า knowledge ทั่วไป / คำถามง่าย / สรุปสั้น → ตอบเลย (0 delegate)\n"
    "- **ขั้น 2:** ถ้าต้องผู้เชี่ยวชาญจริงๆ → delegate **เพียง 1 คน** ที่ตรงที่สุด\n"
    "- **ขั้น 3:** ถ้าโจทย์ซับซ้อนหลายมิติ → delegate 2-3 คนได้ แต่ต้อง justify ในหัวก่อน\n"
    "- **ห้าม:** spawn ทั้งทีม (8 คน) ถ้าบอสไม่ได้ขอ. ห้าม delegate เรื่องที่ตัวเองตอบได้ง่ายๆ\n"
    "- ก่อนสร้างไฟล์/รูป/สไลด์ หรือ delegate หลายคน → ถามบอสก่อน 1 บรรทัดสั้น\n"
    "  เช่น 'ทำเป็นไฟล์ .md หรือสรุป chat ก็พอคะบอส? จะ delegate NOVA หรือ NEO ตอบเองก็พอ?'\n"
    "- งานเล็ก/ชัดเจน → ตอบเลยไม่ต้องถาม. ประหยัด token = ประหยัดเงินบอส"
)


async def orchestrate(
    prompt: str,
    agents_map: dict[str, str],
    root_agent: str = "neo",
    model: str = "claude-sonnet-4-6",
    max_delegations: int = 3,
    max_loops: int = 4,
):
    """Run multi-agent orchestration, yielding events.

    Event shapes:
      {"type": "start",   "agent": <id>}
      {"type": "text",    "agent": <id>, "text": <full text>}
      {"type": "handoff", "from": <id>,  "to": <id>, "task": <str>}
      {"type": "done",    "agent": <id>}
      {"type": "error",   "message": <str>}
    """
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Specialists list excludes the root so NEO can't delegate to itself
    specialist_ids = [a for a in agents_map.keys() if a != root_agent]
    delegate_tool = build_delegate_tool(specialist_ids)

    messages = [{"role": "user", "content": prompt}]
    delegations_used = 0

    yield {"type": "start", "agent": root_agent}

    for _loop in range(max_loops):
        # File tools always available; delegate tool only while under cap
        tools = list(AGENT_TOOLS)
        if delegations_used < max_delegations:
            tools = [delegate_tool] + tools
        try:
            resp = await client.messages.create(
                model=model,
                max_tokens=1200,  # tightened from 2000 — brief synth, long delegate responses come from specialists
                system=agents_map[root_agent] + ORCHESTRATOR_SUFFIX,
                tools=tools if tools else None,
                messages=messages,
            )
        except Exception as e:
            yield {"type": "error", "message": f"root call failed: {e}"}
            return

        # Emit root text before handling any tool calls
        root_text = "".join(
            b.text for b in resp.content if getattr(b, "type", None) == "text"
        ).strip()
        if root_text:
            yield {"type": "text", "agent": root_agent, "text": root_text}

        if resp.stop_reason != "tool_use":
            yield {"type": "done", "agent": root_agent}
            return

        tool_results = []
        for block in resp.content:
            if getattr(block, "type", None) != "tool_use":
                continue

            # --- File tools (write_file / read_file / etc.) ---
            if block.name in TOOL_NAMES:
                result = execute_tool(block.name, dict(block.input))
                yield {
                    "type": "tool_call",
                    "agent": root_agent,
                    "tool": block.name,
                    "input": dict(block.input),
                    "result": result,
                }
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": format_result_for_claude(result),
                    "is_error": not result.get("ok", False),
                })
                continue

            # --- Delegation ---
            if block.name != "delegate":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"unknown tool: {block.name}",
                    "is_error": True,
                })
                continue

            target = (block.input.get("agent") or "").lower()
            task = (block.input.get("task") or "").strip()
            if target not in agents_map or target == root_agent or not task:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"invalid delegation: agent={target}",
                    "is_error": True,
                })
                continue

            delegations_used += 1
            yield {"type": "handoff", "from": root_agent, "to": target, "task": task}
            yield {"type": "start", "agent": target}

            sub_text = ""
            try:
                # Sub-agent runs its own mini tool loop (file tools only, no delegate)
                sub_messages = [{"role": "user", "content": task}]
                sub_system = (
                    agents_map[target]
                    + "\n\n**File Tools:** คุณสามารถ write_file/read_file/edit_file/list_files/make_dir/delete_file "
                      "ใน workspace ได้ — ใช้เมื่อ task ต้องการ output เป็นไฟล์"
                )
                for _sub_loop in range(3):
                    sub = await client.messages.create(
                        model=model,
                        max_tokens=900,  # tightened from 1500
                        system=sub_system,
                        tools=list(AGENT_TOOLS),
                        messages=sub_messages,
                    )
                    piece = "".join(
                        b.text for b in sub.content if getattr(b, "type", None) == "text"
                    ).strip()
                    if piece:
                        sub_text += ("\n\n" if sub_text else "") + piece
                    if sub.stop_reason != "tool_use":
                        break
                    sub_tool_results = []
                    for sb in sub.content:
                        if getattr(sb, "type", None) != "tool_use":
                            continue
                        if sb.name not in TOOL_NAMES:
                            sub_tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": sb.id,
                                "content": f"tool {sb.name} unavailable to specialist",
                                "is_error": True,
                            })
                            continue
                        sub_result = execute_tool(sb.name, dict(sb.input))
                        yield {
                            "type": "tool_call",
                            "agent": target,
                            "tool": sb.name,
                            "input": dict(sb.input),
                            "result": sub_result,
                        }
                        sub_tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": sb.id,
                            "content": format_result_for_claude(sub_result),
                            "is_error": not sub_result.get("ok", False),
                        })
                    sub_messages.append({"role": "assistant", "content": sub.content})
                    sub_messages.append({"role": "user", "content": sub_tool_results})
            except Exception as e:
                sub_text = (sub_text + "\n" if sub_text else "") + f"[specialist error: {e}]"

            yield {"type": "text", "agent": target, "text": sub_text}
            yield {"type": "done", "agent": target}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": sub_text or "(empty)",
            })

        # Feed specialist results back so root can synthesize
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": tool_results})

    # Exceeded max_loops without end_turn
    yield {"type": "done", "agent": root_agent}
