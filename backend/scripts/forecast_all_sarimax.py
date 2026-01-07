from __future__ import annotations

import os

import psycopg
import pandas as pd

from app.db import dsn
from app.ua_oblasts import OBLASTS_ORDERED
from app.data_access.bins import latest_ts

from app.ml.sarimax_core import SarimaxConfig, forecast_probs
from app.ml.model_store import load_model, model_filename

from app.data_access.exog import build_exog_for_uid


HORIZON_HOURS = int(os.getenv("HORIZON_HOURS", "168"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "sarimax_v1_hourly")
MODEL_DIR = os.getenv("MODEL_DIR", "/data/models/sarimax")


def upsert_forecast(oblast_uid: int, model_version: str, df) -> int:
    rows = [
        (oblast_uid, r.ts.to_pydatetime(), float(r.p_alarm), model_version)
        for r in df.itertuples(index=False)
    ]
    if not rows:
        return 0

    with psycopg.connect(dsn()) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO alarm_forecasts_hourly (oblast_uid, ts, p_alarm, model_version)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (oblast_uid, ts, model_version) DO UPDATE
                SET p_alarm = EXCLUDED.p_alarm, created_at = now()
                """,
                rows,
            )
        conn.commit()

    return len(rows)


def main() -> None:
    cfg = SarimaxConfig()

    total_rows = 0
    ok = 0
    skipped = 0

    for o in OBLASTS_ORDERED:
        uid = o.uid
        model_path = os.path.join(MODEL_DIR, model_filename(uid, MODEL_VERSION, cfg))

        if not os.path.exists(model_path):
            print(f"[forecast-all] uid={uid} skip: model not found")
            skipped += 1
            continue

        try:
            res = load_model(model_path)

            last = latest_ts(uid)

            start = last + pd.Timedelta(hours=1)
            future_idx = pd.date_range(start, periods=HORIZON_HOURS, freq="h", tz="UTC")

            exog_future = build_exog_for_uid(uid, future_idx)

            df = forecast_probs(res, exog_future)

            df = df.head(HORIZON_HOURS)

            saved = upsert_forecast(uid, MODEL_VERSION, df)

            print(
                f"[forecast-all] uid={uid} saved={saved} "
                f"from={df.ts.iloc[0].isoformat()} to={df.ts.iloc[-1].isoformat()}"
            )

            total_rows += saved
            ok += 1
        except Exception as e:
            print(f"[forecast-all] uid={uid} error: {e}")

    print(f"[forecast-all] done ok={ok} skipped={skipped} rows={total_rows}")


if __name__ == "__main__":
    main()
