from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from time import time
from datetime import datetime, timezone

from . import alerts_client
from .ua_oblasts import OBLASTS_ORDERED, decode_by_oblast_char
from .storage import BY_OBLAST_SNAPSHOT_FILE


INTERVAL_SECONDS = int(os.getenv("BY_OBLAST_POLL_SECONDS", "120"))

FORECAST_EVERY_SECONDS = int(os.getenv("FORECAST_EVERY_SECONDS", "3600"))
TRAIN_AT_UTC_HOUR = int(os.getenv("TRAIN_AT_UTC_HOUR", "3"))
TRAIN_AT_UTC_MIN = int(os.getenv("TRAIN_AT_UTC_MIN", "30"))

MODEL_DIR = os.getenv("MODEL_DIR", "/data/models/sarimax")

_ml_lock = asyncio.Lock()


def _has_any_models(model_dir: str) -> bool:
    p = Path(model_dir)
    if not p.exists():
        return False
    return any(p.glob("*.pkl")) or any(p.glob("*.pkl.gz"))


async def _run(cmd: list[str], name: str) -> int:
    try:
        print(f"[worker] run {name}: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(*cmd)
        rc = await proc.wait()
        if rc != 0:
            print(f"[worker] {name} failed rc={rc}")
        return rc
    except Exception as e:
        print(f"[worker] {name} error: {e}")
        return 1


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
    BY_OBLAST_SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = BY_OBLAST_SNAPSHOT_FILE.with_suffix(BY_OBLAST_SNAPSHOT_FILE.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(BY_OBLAST_SNAPSHOT_FILE)


async def snapshot_loop() -> None:
    while True:
        try:
            raw = await alerts_client.get_active_air_raid_alerts_by_oblast()
            payload = _normalize_by_oblast(raw)
            await _write_snapshot(payload)
            print(f"[worker] snapshot updated at {payload['updated_at']}")
        except Exception as e:
            print(f"[worker] snapshot error: {e}")

        await asyncio.sleep(INTERVAL_SECONDS)


async def ml_bootstrap() -> None:
    await asyncio.sleep(20)  # let postgres & backend settle

    if _has_any_models(MODEL_DIR):
        print(f"[worker] bootstrap: models exist in {MODEL_DIR}, skip")
        return

    print(f"[worker] bootstrap: no models in {MODEL_DIR}, training")
    async with _ml_lock:
        rc = await _run([sys.executable, "scripts/train_all_sarimax.py"], "train_all")

        if rc == 0 and _has_any_models(MODEL_DIR):
            await _run([sys.executable, "scripts/forecast_all_sarimax.py"], "forecast_all")
        else:
            print("[worker] bootstrap: train failed or models missing")


async def forecast_loop() -> None:
    await asyncio.sleep(30)

    while True:
        if not _has_any_models(MODEL_DIR):
            print("[worker] forecast: no models, skipping")
            await asyncio.sleep(60)
            continue

        async with _ml_lock:
            await _run([sys.executable, "scripts/forecast_all_sarimax.py"], "forecast_all")

        await asyncio.sleep(FORECAST_EVERY_SECONDS)


async def train_daily_loop() -> None:
    await asyncio.sleep(60)
    last_day: str | None = None

    while True:
        now = datetime.now(timezone.utc)

        if now.hour == TRAIN_AT_UTC_HOUR and now.minute == TRAIN_AT_UTC_MIN:
            day = now.date().isoformat()
            if day != last_day:
                async with _ml_lock:
                    rc_load = await _run([sys.executable, "scripts/load_data.py"], "load_data")
                    if rc_load != 0:
                        print("[worker] daily-train: load_data failed; skipping train for today")
                    else:
                        rc_tr = await _run([sys.executable, "scripts/train_all_sarimax.py"], "train_all")
                        if rc_tr == 0:
                            await _run([sys.executable, "scripts/forecast_all_sarimax.py"], "forecast_all")

                last_day = day

        await asyncio.sleep(30)


async def main() -> None:
    await asyncio.gather(
        snapshot_loop(),
        ml_bootstrap(),
        forecast_loop(),
        train_daily_loop(),
    )


if __name__ == "__main__":
    asyncio.run(main())
