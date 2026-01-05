from __future__ import annotations

from fastapi import APIRouter
from ..db import get_conn
from ..ua_oblasts import OBLASTS_ORDERED

router = APIRouter(prefix="/db", tags=["db"])


@router.get("/stats/oblasts")
def oblasts_import_and_bins_stats():
    stats = {
        o.uid: {
            "uid": o.uid,
            "name": o.name,
            "events_count": 0,
            "events_started_min": None,
            "events_finished_max": None,
            "bins_count": 0,
            "bins_ts_min": None,
            "bins_ts_max": None,
            "bins_alarm_count": 0,
            "bins_alarm_ratio": 0.0,
        }
        for o in OBLASTS_ORDERED
    }

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    oblast_uid,
                    COUNT(*)::bigint AS events_count,
                    MIN(started_at) AS events_started_min,
                    MAX(finished_at) AS events_finished_max
                FROM alarm_events_oblast
                GROUP BY oblast_uid
                """
            )
            for uid, cnt, smin, fmax in cur.fetchall():
                if uid in stats:
                    stats[uid]["events_count"] = int(cnt)
                    stats[uid]["events_started_min"] = smin.isoformat() if smin else None
                    stats[uid]["events_finished_max"] = fmax.isoformat() if fmax else None

            cur.execute(
                """
                SELECT
                    oblast_uid,
                    COUNT(*)::bigint AS bins_count,
                    MIN(ts) AS bins_ts_min,
                    MAX(ts) AS bins_ts_max,
                    SUM(CASE WHEN is_alarm = 1 THEN 1 ELSE 0 END)::bigint AS bins_alarm_count
                FROM alarm_bins_oblast
                GROUP BY oblast_uid
                """
            )
            for uid, bins_cnt, tmin, tmax, alarm_cnt in cur.fetchall():
                if uid in stats:
                    bins_cnt_i = int(bins_cnt)
                    alarm_cnt_i = int(alarm_cnt or 0)

                    stats[uid]["bins_count"] = bins_cnt_i
                    stats[uid]["bins_ts_min"] = tmin.isoformat() if tmin else None
                    stats[uid]["bins_ts_max"] = tmax.isoformat() if tmax else None
                    stats[uid]["bins_alarm_count"] = alarm_cnt_i
                    stats[uid]["bins_alarm_ratio"] = (alarm_cnt_i / bins_cnt_i) if bins_cnt_i else 0.0

    return {"items": [stats[o.uid] for o in OBLASTS_ORDERED]}


@router.get("/oblast/{uid}/bins_head")
def bins_head(uid: int, limit: int = 50):
    limit = max(1, min(limit, 500))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ts, is_alarm
                FROM alarm_bins_oblast
                WHERE oblast_uid=%s
                ORDER BY ts
                LIMIT %s
                """,
                (uid, limit),
            )
            rows = cur.fetchall()

    return [{"ts": r[0].isoformat(), "is_alarm": int(r[1])} for r in rows]
