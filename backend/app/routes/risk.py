from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg
from fastapi import APIRouter, HTTPException, Query

from app.db import dsn
from app.ua_oblasts import OBLASTS_ORDERED


router = APIRouter(prefix="/risk", tags=["risk"])

DEFAULT_MODEL_VERSION = os.getenv("MODEL_VERSION", "sarimax_v1_hourly")

DEFAULT_HORIZONS = (6, 24, 168)


def _ceil_to_next_hour_utc(dt: datetime) -> datetime:
    dt = dt.astimezone(timezone.utc)
    dt0 = dt.replace(minute=0, second=0, microsecond=0)
    if dt == dt0:
        return dt0
    return dt0 + timedelta(hours=1)


def risk_any(ps: list[float]) -> float:
    prod = 1.0
    for p in ps:
        p = 0.0 if p < 0 else 1.0 if p > 1 else p
        prod *= (1.0 - p)
    return 1.0 - prod


def expected_alarm_hours(ps: list[float]) -> float:
    return float(sum(ps))


def top_peaks(series: list[dict[str, Any]], k: int = 3) -> list[dict[str, Any]]:
    return sorted(series, key=lambda x: float(x["p_alarm"]), reverse=True)[:k]


def fetch_forecast_series(
    oblast_uid: int,
    model_version: str,
    start_ts: datetime,
    hours: int,
) -> tuple[list[dict[str, Any]], datetime | None]:
    end_ts = start_ts + timedelta(hours=hours - 1)

    with psycopg.connect(dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ts, p_alarm, created_at
                FROM alarm_forecasts_hourly
                WHERE oblast_uid = %s
                  AND model_version = %s
                  AND ts >= %s AND ts <= %s
                ORDER BY ts ASC
                """,
                (oblast_uid, model_version, start_ts, end_ts),
            )
            rows = cur.fetchall()

    if not rows:
        return [], None

    series: list[dict[str, Any]] = []
    latest_created_at: datetime | None = None

    for ts, p_alarm, created_at in rows:
        p = float(p_alarm)
        if p < 0:
            p = 0.0
        elif p > 1:
            p = 1.0

        series.append({"ts": ts.isoformat(), "p_alarm": p})

        if latest_created_at is None or created_at > latest_created_at:
            latest_created_at = created_at

    return series, latest_created_at


@router.get("/oblast/{uid}")
def oblast_risk(
    uid: int,
    horizons: str = Query("6,24,168", description="Comma-separated: e.g. 6,24,168"),
    series_hours: int = Query(168, ge=1, le=336),
    model_version: str = Query(DEFAULT_MODEL_VERSION),
):
    try:
        hs = tuple(int(x.strip()) for x in horizons.split(",") if x.strip())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid horizons format")
    if not hs:
        hs = DEFAULT_HORIZONS

    now = datetime.now(timezone.utc)
    start = _ceil_to_next_hour_utc(now)

    series, generated_at = fetch_forecast_series(
        oblast_uid=uid,
        model_version=model_version,
        start_ts=start,
        hours=series_hours,
    )

    if not series:
        raise HTTPException(
            status_code=503,
            detail="Forecast not ready yet for this oblast/model. Run forecast job first.",
        )

    ps = [float(x["p_alarm"]) for x in series]

    summary: dict[str, Any] = {}
    for h in hs:
        if h <= 0:
            continue

        window = ps[: min(h, len(ps))]
        window_series = series[: min(h, len(series))]

        summary[f"h{h}"] = {
            "risk_any": risk_any(window),
            "expected_alarm_hours": expected_alarm_hours(window),
            "peak_hours": top_peaks(window_series, k=3),
        }

    resp = {
        "oblast_uid": uid,
        "model_version": model_version,
        "generated_at": generated_at.isoformat() if generated_at else None,
        "horizon_start": series[0]["ts"],
        "horizon_end": series[-1]["ts"],
        "series": series,
        "summary": summary,
    }
    return resp


@router.get("/oblasts")
def oblasts_risk(
    horizon_hours: int = Query(6, ge=1, le=168),
    model_version: str = Query(DEFAULT_MODEL_VERSION),
    peaks: int = Query(3, ge=0, le=10),
):
    now = datetime.now(timezone.utc)
    start = _ceil_to_next_hour_utc(now)
    end = start + timedelta(hours=horizon_hours - 1)

    with psycopg.connect(dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT oblast_uid, ts, p_alarm, created_at
                FROM alarm_forecasts_hourly
                WHERE model_version = %s
                  AND ts >= %s AND ts <= %s
                ORDER BY oblast_uid ASC, ts ASC
                """,
                (model_version, start, end),
            )
            rows = cur.fetchall()

    by_uid: dict[int, list[dict[str, Any]]] = {}
    generated_at_by_uid: dict[int, datetime] = {}

    for oblast_uid, ts, p_alarm, created_at in rows:
        p = float(p_alarm)
        if p < 0:
            p = 0.0
        elif p > 1:
            p = 1.0

        by_uid.setdefault(int(oblast_uid), []).append({"ts": ts.isoformat(), "p_alarm": p})

        prev = generated_at_by_uid.get(int(oblast_uid))
        if prev is None or created_at > prev:
            generated_at_by_uid[int(oblast_uid)] = created_at

    items: list[dict[str, Any]] = []

    for o in OBLASTS_ORDERED:
        series = by_uid.get(o.uid, [])
        if not series:
            items.append(
                {
                    "oblast_uid": o.uid,
                    "oblast_name": o.name,
                    "model_version": model_version,
                    "generated_at": None,
                    "horizon_start": start.isoformat(),
                    "horizon_end": end.isoformat(),
                    "risk_any": None,
                    "expected_alarm_hours": None,
                    "peak_hours": [],
                    "has_data": False,
                }
            )
            continue

        ps = [float(x["p_alarm"]) for x in series]

        items.append(
            {
                "oblast_uid": o.uid,
                "oblast_name": o.name,
                "model_version": model_version,
                "generated_at": generated_at_by_uid.get(o.uid).isoformat() if generated_at_by_uid.get(o.uid) else None,
                "horizon_start": series[0]["ts"],
                "horizon_end": series[-1]["ts"],
                "risk_any": risk_any(ps),
                "expected_alarm_hours": expected_alarm_hours(ps),
                "peak_hours": top_peaks(series, k=peaks) if peaks > 0 else [],
                "has_data": True,
            }
        )

    return {
        "model_version": model_version,
        "horizon_hours": horizon_hours,
        "horizon_start": start.isoformat(),
        "horizon_end": end.isoformat(),
        "items": items,
    }
