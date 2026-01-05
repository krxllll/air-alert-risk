from __future__ import annotations

import asyncio
import json
import os
from time import time

from . import alerts_client
from .ua_oblasts import OBLASTS_ORDERED, decode_by_oblast_char
from .storage import BY_OBLAST_SNAPSHOT_PATH

INTERVAL_SECONDS = int(os.getenv("BY_OBLAST_POLL_SECONDS", "120"))


def _normalize_by_oblast(raw) -> dict:
    s = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
    if not isinstance(s, str):
        raise RuntimeError("Unexpected by_oblast response type")

    if len(s) < len(OBLASTS_ORDERED):
        raise RuntimeError(f"by_oblast string too short: {len(s)}")

    items = []
    for idx, oblast in enumerate(OBLASTS_ORDERED):
        ch = s[idx]
        items.append(
            {
                "uid": oblast.uid,
                "name": oblast.name,
                "status": decode_by_oblast_char(ch),
            }
        )

    return {
        "origin": "alerts.in.ua",
        "mode": "snapshot",
        "updated_at": int(time()),
        "items": items,
    }


async def _write_snapshot(payload: dict) -> None:
    os.makedirs(os.path.dirname(BY_OBLAST_SNAPSHOT_PATH), exist_ok=True)
    tmp = BY_OBLAST_SNAPSHOT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, BY_OBLAST_SNAPSHOT_PATH)


async def run() -> None:
    while True:
        try:
            raw = await alerts_client.get_active_air_raid_alerts_by_oblast()
            payload = _normalize_by_oblast(raw)
            await _write_snapshot(payload)
            print(f"[worker] snapshot updated at {payload['updated_at']}")
        except Exception as e:
            print(f"[worker] error: {e}")

        await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
