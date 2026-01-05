from __future__ import annotations
from time import time
import json
import os
from fastapi import APIRouter, HTTPException
from .. import alerts_client
from ..ua_oblasts import OBLASTS_ORDERED, decode_by_oblast_char
from ..cache import cache
from ..storage import BY_OBLAST_SNAPSHOT_PATH
from ..snapshot import read_by_oblast_snapshot

router = APIRouter(prefix="/ua", tags=["ukraine"])

BY_OBLAST_CACHE_KEY = "alerts:by_oblast"
BY_OBLAST_TTL_SECONDS = 60


@router.get("/oblasts")
def oblasts():
    return [{"uid": o.uid, "name": o.name} for o in OBLASTS_ORDERED]


@router.get("/alerts/oblasts/statuses")
async def oblast_statuses():
    snap = read_by_oblast_snapshot()
    if snap is not None:
        return snap

    cached = cache.get(BY_OBLAST_CACHE_KEY)
    if cached is not None and cache.is_fresh(cached):
        return cached.value

    try:
        raw = await alerts_client.get_active_air_raid_alerts_by_oblast()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    s = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
    if not isinstance(s, str):
        raise HTTPException(status_code=502, detail="Unexpected by_oblast response type")

    if len(s) < len(OBLASTS_ORDERED):
        raise HTTPException(
            status_code=502,
            detail=f"by_oblast string too short: {len(s)} < {len(OBLASTS_ORDERED)}",
        )

    items = []
    for idx, oblast in enumerate(OBLASTS_ORDERED):
        ch = s[idx]
        items.append(
            {
                "uid": oblast.uid,
                "name": oblast.name,
                "status": decode_by_oblast_char(ch),
                # "raw": ch,
            }
        )

    response = {
        "origin": "alerts.in.ua",
        "mode": "live_fallback",
        "updated_at": int(time()),
        "ttl_seconds": BY_OBLAST_TTL_SECONDS,
        "items": items,
    }

    cache.set(BY_OBLAST_CACHE_KEY, response, ttl_seconds=BY_OBLAST_TTL_SECONDS)
    return response


@router.get("/alerts/oblasts/statuses_live")
async def oblast_statuses_live():
    cached = cache.get(BY_OBLAST_CACHE_KEY)
    if cached is not None and cache.is_fresh(cached):
        return cached.value

    try:
        raw = await alerts_client.get_active_air_raid_alerts_by_oblast()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    s = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
    if not isinstance(s, str):
        raise HTTPException(status_code=502, detail="Unexpected by_oblast response type")

    items = []
    for idx, oblast in enumerate(OBLASTS_ORDERED):
        ch = s[idx]
        items.append(
            {"uid": oblast.uid, "name": oblast.name, "status": decode_by_oblast_char(ch)}
        )

    response = {
        "origin": "alerts.in.ua",
        "mode": "live",
        "updated_at": int(time()),
        "ttl_seconds": BY_OBLAST_TTL_SECONDS,
        "items": items,
    }
    cache.set(BY_OBLAST_CACHE_KEY, response, ttl_seconds=BY_OBLAST_TTL_SECONDS)
    return response


@router.get("/alerts/oblasts/status/{uid}")
async def oblast_status(uid: int):
    statuses = await oblast_statuses()
    for item in statuses:
        if item["uid"] == uid:
            return item
    raise HTTPException(status_code=404, detail="Unknown oblast uid")


@router.get("/alerts/oblasts/statuses_snapshot")
def oblast_statuses_snapshot():
    if not os.path.exists(BY_OBLAST_SNAPSHOT_PATH):
        raise HTTPException(status_code=503, detail="Snapshot not ready yet")

    try:
        with open(BY_OBLAST_SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
