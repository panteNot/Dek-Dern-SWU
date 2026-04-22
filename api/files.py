"""File Manager service — path-safe file operations limited to WORKSPACE root."""
from pathlib import Path
from fastapi import HTTPException
import os

# Sandbox root — ป้องกัน File Manager เห็นไฟล์นอก workspace
WORKSPACE = Path(os.getenv("NEO_WORKSPACE", Path(__file__).parent.parent / "workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ไฟล์ประเภทที่ treat เป็น binary (ไม่อ่าน content)
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
              ".zip", ".mp4", ".mp3", ".woff", ".woff2", ".ttf"}
MAX_READ_SIZE = 2 * 1024 * 1024  # 2MB limit


def resolve_safe(rel_path: str) -> Path:
    """Resolve รให้ absolute path + กัน path traversal (../../etc/passwd)."""
    rel = (rel_path or "").lstrip("/")
    target = (WORKSPACE / rel).resolve()
    if not str(target).startswith(str(WORKSPACE)):
        raise HTTPException(status_code=403, detail="path escapes workspace")
    return target


def list_tree(rel_path: str = "", depth: int = 3) -> dict:
    """Walk directory → return nested dict."""
    root = resolve_safe(rel_path)
    if not root.exists():
        raise HTTPException(status_code=404, detail="path not found")

    def walk(p: Path, d: int):
        try:
            rel = str(p.relative_to(WORKSPACE)) or "."
        except ValueError:
            rel = str(p)
        if p.is_dir():
            node = {"name": p.name or "workspace", "path": rel, "type": "dir", "children": []}
            if d > 0:
                try:
                    kids = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
                    for child in kids:
                        if child.name.startswith("."):
                            continue
                        node["children"].append(walk(child, d - 1))
                except PermissionError:
                    pass
            return node
        return {
            "name": p.name, "path": rel, "type": "file",
            "size": p.stat().st_size, "ext": p.suffix.lower(),
        }
    return walk(root, depth)


def read_file(rel_path: str) -> dict:
    """อ่าน file content (text only for non-binary)."""
    target = resolve_safe(rel_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="file not found")
    if target.is_dir():
        raise HTTPException(status_code=400, detail="is a directory")
    size = target.stat().st_size
    if size > MAX_READ_SIZE:
        raise HTTPException(status_code=413, detail="file too large")
    ext = target.suffix.lower()
    if ext in BINARY_EXT:
        return {"path": rel_path, "type": "binary", "size": size, "ext": ext}
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"path": rel_path, "type": "binary", "size": size, "ext": ext}
    return {"path": rel_path, "type": "text", "size": size, "ext": ext, "content": content}


def write_file(rel_path: str, content: str) -> dict:
    """เขียน file — สร้าง parent dirs ถ้าไม่มี."""
    target = resolve_safe(rel_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": rel_path, "size": target.stat().st_size, "ok": True}


def make_dir(rel_path: str) -> dict:
    target = resolve_safe(rel_path)
    target.mkdir(parents=True, exist_ok=True)
    return {"path": rel_path, "ok": True}


def delete_path(rel_path: str) -> dict:
    target = resolve_safe(rel_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="not found")
    if target == WORKSPACE:
        raise HTTPException(status_code=403, detail="cannot delete workspace root")
    if target.is_dir():
        import shutil
        shutil.rmtree(target)
    else:
        target.unlink()
    return {"path": rel_path, "ok": True}
