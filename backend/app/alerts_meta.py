from __future__ import annotations

import os
from pathlib import Path

META_DIR = Path(os.getenv("HTTP_CACHE_DIR", "/data/runtime/http_cache"))
META_DIR.mkdir(parents=True, exist_ok=True)

def _safe_name(key: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in key)

def read_last_modified(key: str) -> str | None:
    p = META_DIR / f"{_safe_name(key)}.last_modified.txt"
    if not p.exists():
        return None
    v = p.read_text(encoding="utf-8").strip()
    return v or None

def write_last_modified(key: str, value: str) -> None:
    p = META_DIR / f"{_safe_name(key)}.last_modified.txt"
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(value, encoding="utf-8")
    os.replace(tmp, p)
