"""Claude tool definitions + dispatcher for file operations.

Wraps the existing files.py helpers as Claude tool_use schemas so agents can
read/write/edit files in the sandboxed WORKSPACE. All paths are relative to
WORKSPACE root and resolved through files.resolve_safe() to prevent escape.
"""
from __future__ import annotations
import files


AGENT_TOOLS = [
    {
        "name": "write_file",
        "description": (
            "Create or overwrite a file in the workspace. Creates parent "
            "directories automatically. Use when the user asks to save/create/"
            "generate a file. Always prefer descriptive paths like "
            "'projects/launch/plan.md' over flat 'file1.md'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path within workspace, e.g. 'notes/plan.md'",
                },
                "content": {
                    "type": "string",
                    "description": "Full file content. UTF-8 text.",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "description": (
            "Read the text content of a file in the workspace. Returns content "
            "for text files, or metadata only for binary. Use before editing "
            "to see current state."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path within workspace"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "edit_file",
        "description": (
            "Edit an existing file by replacing `old_text` with `new_text`. "
            "`old_text` must appear exactly once in the file. Preserves the "
            "rest of the file unchanged. Use for small targeted edits instead "
            "of rewriting the whole file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string", "description": "Exact text to find (must be unique)"},
                "new_text": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    {
        "name": "list_files",
        "description": (
            "List files and folders in the workspace (or a subpath). Returns "
            "nested tree up to the given depth. Use to explore what exists "
            "before creating new files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Subpath from workspace root. Empty = root.", "default": ""},
                "depth": {"type": "integer", "description": "Tree depth, 1-4", "default": 2},
            },
        },
    },
    {
        "name": "make_dir",
        "description": "Create a directory (and any missing parents) in the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path, e.g. 'projects/launch/'"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "delete_file",
        "description": (
            "Delete a file or directory (recursively) in the workspace. "
            "Destructive — only use when the user explicitly asks to delete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    },
]


TOOL_NAMES = {t["name"] for t in AGENT_TOOLS}


def execute_tool(name: str, inp: dict) -> dict:
    """Dispatch a tool call and return a structured result.

    Returns on success: {"ok": True, ...data}
    Returns on error:   {"ok": False, "error": "<msg>"}
    Never raises — HTTPException from files.py is caught and converted.
    """
    try:
        if name == "write_file":
            path = (inp.get("path") or "").strip()
            content = inp.get("content") or ""
            if not path:
                return {"ok": False, "error": "missing path"}
            res = files.write_file(path, content)
            return {"ok": True, "tool": name, "path": res["path"], "size": res["size"]}

        elif name == "read_file":
            path = (inp.get("path") or "").strip()
            if not path:
                return {"ok": False, "error": "missing path"}
            res = files.read_file(path)
            if res.get("type") == "binary":
                return {"ok": True, "tool": name, "path": path, "binary": True, "size": res["size"]}
            return {
                "ok": True,
                "tool": name,
                "path": path,
                "size": res["size"],
                "content": res["content"],
            }

        elif name == "edit_file":
            path = (inp.get("path") or "").strip()
            old_text = inp.get("old_text") or ""
            new_text = inp.get("new_text") or ""
            if not path or not old_text:
                return {"ok": False, "error": "missing path or old_text"}
            current = files.read_file(path)
            if current.get("type") != "text":
                return {"ok": False, "error": "file is binary or unreadable"}
            body = current["content"]
            occurrences = body.count(old_text)
            if occurrences == 0:
                return {"ok": False, "error": "old_text not found in file"}
            if occurrences > 1:
                return {"ok": False, "error": f"old_text appears {occurrences} times — must be unique"}
            updated = body.replace(old_text, new_text, 1)
            res = files.write_file(path, updated)
            return {
                "ok": True,
                "tool": name,
                "path": path,
                "size": res["size"],
                "replaced": 1,
            }

        elif name == "list_files":
            path = (inp.get("path") or "").strip()
            depth = int(inp.get("depth") or 2)
            depth = max(1, min(depth, 4))
            tree = files.list_tree(path, depth)
            return {"ok": True, "tool": name, "tree": tree}

        elif name == "make_dir":
            path = (inp.get("path") or "").strip()
            if not path:
                return {"ok": False, "error": "missing path"}
            files.make_dir(path)
            return {"ok": True, "tool": name, "path": path}

        elif name == "delete_file":
            path = (inp.get("path") or "").strip()
            if not path:
                return {"ok": False, "error": "missing path"}
            files.delete_path(path)
            return {"ok": True, "tool": name, "path": path, "deleted": True}

        else:
            return {"ok": False, "error": f"unknown tool: {name}"}

    except Exception as e:
        # Catches HTTPException (403 path escape, 404 not found, etc.) + any other
        detail = getattr(e, "detail", None) or str(e)
        return {"ok": False, "error": str(detail), "tool": name}


def format_result_for_claude(result: dict) -> str:
    """Serialize tool result as concise text for the Claude tool_result block.

    Keeps the agent's input tokens low — don't dump full file content unless
    it's a read_file call (agent needs to see content to act on it).
    """
    if not result.get("ok"):
        return f"ERROR: {result.get('error', 'unknown')}"

    tool = result.get("tool", "")
    if tool == "write_file":
        return f"OK: wrote {result['path']} ({result['size']} bytes)"
    if tool == "read_file":
        if result.get("binary"):
            return f"BINARY file {result['path']} ({result['size']} bytes) — cannot read"
        return f"FILE {result['path']} ({result['size']} bytes):\n---\n{result.get('content','')}"
    if tool == "edit_file":
        return f"OK: edited {result['path']} ({result['replaced']} replacement, {result['size']} bytes)"
    if tool == "list_files":
        import json
        return "TREE:\n" + json.dumps(result["tree"], ensure_ascii=False, indent=2)[:4000]
    if tool == "make_dir":
        return f"OK: created directory {result['path']}"
    if tool == "delete_file":
        return f"OK: deleted {result['path']}"
    return "OK"
