from __future__ import annotations

import pandas as pd
import psycopg
from app.db import dsn


def load_bins_series(uid: int) -> pd.Series:
    with psycopg.connect(dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ts, is_alarm
                FROM alarm_bins_oblast
                WHERE oblast_uid=%s
                ORDER BY ts
                """,
                (uid,),
            )
            rows = cur.fetchall()

    if not rows:
        raise RuntimeError("No bins found for this oblast_uid")

    df = pd.DataFrame(rows, columns=["ts", "is_alarm"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.set_index("ts")

    idx = pd.date_range(df.index.min(), df.index.max(), freq="h", tz="UTC")
    df = df.reindex(idx)
    df["is_alarm"] = df["is_alarm"].fillna(0).astype(int)
    return df["is_alarm"]


def latest_ts(uid: int) -> pd.Timestamp:
    y = load_bins_series(uid)
    return y.index.max()
