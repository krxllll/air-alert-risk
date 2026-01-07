from __future__ import annotations

import os
import time
import pandas as pd

from app.data_access.bins import load_bins_series
from app.data_access.exog import build_exog_for_uid
from app.ml.model_store import ensure_dir, load_model, model_filename, save_model
from app.ml.sarimax_core import SarimaxConfig, fit_sarimax


UID = int(os.getenv("TRAIN_UID", "14"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "sarimax_v1_hourly")
MODEL_DIR = os.getenv("MODEL_DIR", "/data/models/sarimax")

WARM_MAXITER = int(os.getenv("WARM_MAXITER", "120"))
FALLBACK_MAXITER = int(os.getenv("FALLBACK_MAXITER", "200"))

LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "0"))


def _apply_lookback(y: pd.Series, days: int) -> pd.Series:
    if days <= 0:
        return y
    end = y.index.max()
    start = end - pd.Timedelta(days=days) + pd.Timedelta(hours=1)
    y2 = y.loc[start:end]
    if len(y2) < 24 * 30:
        raise RuntimeError(f"LOOKBACK_DAYS={days} leaves too little data: n={len(y2)}")
    return y2


def main() -> None:
    y_full = load_bins_series(UID)
    y = _apply_lookback(y_full, LOOKBACK_DAYS)

    exog = build_exog_for_uid(UID, y.index)

    cfg = SarimaxConfig()
    ensure_dir(MODEL_DIR)

    extra = {"lookback_days": LOOKBACK_DAYS} if LOOKBACK_DAYS > 0 else None
    path = os.path.join(MODEL_DIR, model_filename(UID, MODEL_VERSION, cfg, extra=extra))

    start_params = None
    if os.path.exists(path) or os.path.exists(path + ".gz"):
        prev = load_model(path)
        start_params = getattr(prev, "params", None)
        print(f"[train] warm-start from existing model: {path} (or .gz)")
    else:
        print("[train] no previous model found for this signature (cold start)")

    print(
        f"[train] uid={UID} model_version={MODEL_VERSION} lookback_days={LOOKBACK_DAYS} "
        f"n={len(y)} (full_n={len(y_full)})"
    )

    t0 = time.time()
    res = fit_sarimax(
        y=y,
        exog=exog,
        cfg=cfg,
        start_params=start_params,
        maxiter_override=WARM_MAXITER if start_params is not None else FALLBACK_MAXITER,
    )

    converged = getattr(res, "mle_retvals", {}).get("converged", True)
    print(f"[train] converged={converged} maxiter_used={'warm' if start_params is not None else 'cold'}")

    if start_params is not None and not converged and FALLBACK_MAXITER > WARM_MAXITER:
        print(f"[train] warm-start did not converge, retrying with maxiter={FALLBACK_MAXITER}")
        res = fit_sarimax(
            y=y,
            exog=exog,
            cfg=cfg,
            start_params=start_params,
            maxiter_override=FALLBACK_MAXITER,
        )
        converged2 = getattr(res, "mle_retvals", {}).get("converged", True)
        print(f"[train] converged_after_fallback={converged2}")

    save_model(res, path)
    print(f"[train] saved: {path} (or .gz if enabled)")
    print(f"[train] seconds={time.time() - t0:.1f}")
    print(f"[train] series_max_ts: {y.index.max().isoformat()}")


if __name__ == "__main__":
    main()
