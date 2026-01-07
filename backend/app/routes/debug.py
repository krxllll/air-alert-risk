from __future__ import annotations

import os
import json
from time import time
from fastapi import APIRouter, HTTPException
from ..cache import cache
from ..storage import BY_OBLAST_SNAPSHOT_FILE

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/snapshot/by_oblast")
def snapshot_by_oblast_info():
    if not os.path.exists(BY_OBLAST_SNAPSHOT_FILE):
        return {
            "ready": False,
            "path": BY_OBLAST_SNAPSHOT_FILE,
            "reason": "file_not_found",
        }

    try:
        with open(BY_OBLAST_SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        updated_at = data.get("updated_at")
        age_seconds = int(time() - updated_at) if isinstance(updated_at, int) else None

        return {
            "ready": True,
            "path": BY_OBLAST_SNAPSHOT_FILE,
            "updated_at": updated_at,
            "age_seconds": age_seconds,
            "source": data.get("source"),
            "items_count": len(data.get("items", [])) if isinstance(data.get("items"), list) else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
def clear_cache():
    cache.clear()
    return {"ok": True}
