from __future__ import annotations

import os
from datetime import timedelta

import pandas as pd
import psycopg

from app.db import dsn
from app.data_access.bins import load_bins_series, latest_ts
from app.data_access.exog import build_exog_for_uid
from app.ml.model_store import load_model, model_filename
from app.ml.sarimax_core import SarimaxConfig, forecast_probs


UID = int(os.getenv("UID", "14"))
HORIZON_HOURS = int(os.getenv("HORIZON_HOURS", "168"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "sarimax_v1_hourly")
MODEL_DIR = os.getenv("MODEL_DIR", "/data/models/sarimax")


def upsert_forecast(uid: int, model_version: str, df: pd.DataFrame) -> None:
    rows = [
        (uid, r.ts.to_pydatetime(), float(r.p_alarm), model_version)
        for r in df.itertuples(index=False)
    ]
    with psycopg.connect(dsn()) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO alarm_forecasts_hourly (oblast_uid, ts, p_alarm, model_version)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (oblast_uid, ts, model_version) DO UPDATE
                SET p_alarm=EXCLUDED.p_alarm, created_at=now()
                """,
                rows,
            )
        conn.commit()


def main() -> None:
    cfg = SarimaxConfig()
    path = os.path.join(MODEL_DIR, model_filename(UID, MODEL_VERSION, cfg))

    if not os.path.exists(path):
        raise RuntimeError(f"Model not found: {path}. Train first (train_sarimax.py).")

    res = load_model(path)

    last = latest_ts(UID)
    future_idx = pd.date_range(
        last + timedelta(hours=1),
        periods=HORIZON_HOURS,
        freq="h",
        tz="UTC",
    )

    y_hist = load_bins_series(UID)
    context_start = y_hist.index.min()
    context_end = future_idx.max()

    context_idx = pd.date_range(context_start, context_end, freq="h", tz="UTC")

    exog_ctx = build_exog_for_uid(UID, context_idx)
    exog_future = exog_ctx.loc[future_idx]

    df = forecast_probs(res, exog_future)

    upsert_forecast(UID, MODEL_VERSION, df)

    print(
        f"[forecast] uid={UID} model_version={MODEL_VERSION} "
        f"from={df.ts.iloc[0].isoformat()} to={df.ts.iloc[-1].isoformat()} saved={len(df)}"
    )


if __name__ == "__main__":
    main()
