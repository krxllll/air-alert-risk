from __future__ import annotations

from .alerts_fetcher import fetch_json


async def get_active_alerts():
    return await fetch_json(
        key="alerts:active",
        path="/v1/alerts/active.json",
        ttl_seconds=60,
    )


async def get_active_air_raid_alerts_by_oblast():
    return await fetch_json(
        key="iot:by_oblast",
        path="/v1/iot/active_air_raid_alerts_by_oblast.json",
        ttl_seconds=60,
    )


async def get_active_air_raid_alert(uid: str):
    return await fetch_json(
        key=f"iot:uid:{uid}",
        path=f"/v1/iot/active_air_raid_alerts/{uid}.json",
        ttl_seconds=60,
    )


async def get_active_air_raid_alerts_all():
    return await fetch_json(
        key="iot:all",
        path="/v1/iot/active_air_raid_alerts.json",
        ttl_seconds=300,
    )


async def get_region_alerts_history(uid: str, period: str):
    return await fetch_json(
        key=f"regions:{uid}:history:{period}",
        path=f"/v1/regions/{uid}/alerts/{period}.json",
        ttl_seconds=60 * 30,
    )
