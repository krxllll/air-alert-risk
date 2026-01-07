from __future__ import annotations

import os
import time

import numpy as np
import pandas as pd

from app.data_access.bins import load_bins_series
from app.data_access.exog import build_exog_for_uid
from app.ml.metrics import (
    roc_auc,
    brier,
    risk_any,
    horizon_labels,
    clip01,
    average_precision,
    logloss,
    precision_recall_f1,
    confusion,
)
from app.ml.model_store import ensure_dir, model_filename, save_model, load_model
from app.ml.sarimax_core import SarimaxConfig, fit_sarimax


UID = int(os.getenv("BT_UID", "14"))
SPLIT_TS = os.getenv("BT_SPLIT_TS", "2025-10-01T00:00:00+00:00")
TEST_DAYS = int(os.getenv("BT_TEST_DAYS", "60"))

MODEL_VERSION = os.getenv("BT_MODEL_VERSION", "sarimax_v1_hourly")
BACKTEST_DIR = os.getenv("BACKTEST_DIR", "/data/backtests/sarimax")

USE_PROD_WARMSTART = os.getenv("BT_USE_PROD_WARMSTART", "1") == "1"
PROD_MODEL_DIR = os.getenv("MODEL_DIR", "/data/models/sarimax")

WARM_MAXITER = int(os.getenv("BT_WARM_MAXITER", "120"))
FALLBACK_MAXITER = int(os.getenv("BT_FALLBACK_MAXITER", "200"))

HOURLY_THRESHOLDS = tuple(
    float(x.strip())
    for x in os.getenv("BT_HOURLY_THRESHOLDS", "0.3,0.5").split(",")
    if x.strip()
)
HORIZON_THRESHOLDS = tuple(
    float(x.strip())
    for x in os.getenv("BT_HORIZON_THRESHOLDS", "0.4,0.6").split(",")
    if x.strip()
)


def _to_utc_ts(s: str) -> pd.Timestamp:
    ts = pd.Timestamp(s)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts


def _print_cls_metrics(prefix: str, y_true: np.ndarray, p: np.ndarray, thresholds: tuple[float, ...]) -> None:
    print(
        f"{prefix}: "
        f"AUC={roc_auc(y_true, p):.4f} "
        f"AP={average_precision(y_true, p):.4f} "
        f"Brier={brier(y_true, p):.4f} "
        f"LogLoss={logloss(y_true, p):.4f}"
    )

    for thr in thresholds:
        y_pred = (p >= thr).astype(int)
        prf = precision_recall_f1(y_true, y_pred)
        c = confusion(y_true, y_pred)
        print(
            f"{prefix}@thr={thr:.2f}: "
            f"acc={prf['accuracy']:.4f} "
            f"prec={prf['precision']:.4f} "
            f"rec={prf['recall']:.4f} "
            f"f1={prf['f1']:.4f} "
            f"spec={prf['specificity']:.4f} "
            f"cm(tp={c['tp']}, fp={c['fp']}, tn={c['tn']}, fn={c['fn']})"
        )


def main() -> None:
    y = load_bins_series(UID)

    split_ts = _to_utc_ts(SPLIT_TS)
    if split_ts <= y.index.min() or split_ts >= y.index.max():
        raise RuntimeError("BT_SPLIT_TS outside series range")

    test_end_ts = split_ts + pd.Timedelta(days=TEST_DAYS)
    if test_end_ts > y.index.max():
        test_end_ts = y.index.max()

    train = y.loc[: split_ts - pd.Timedelta(hours=1)]
    test = y.loc[split_ts:test_end_ts]

    print(f"[bt] uid={UID}")
    print(f"[bt] train: {train.index.min().isoformat()} .. {train.index.max().isoformat()} n={len(train)}")
    print(f"[bt] test : {test.index.min().isoformat()} .. {test.index.max().isoformat()} n={len(test)}")

    cfg = SarimaxConfig()
    ensure_dir(BACKTEST_DIR)

    extra = {"split": SPLIT_TS, "test_days": TEST_DAYS, "exog": "time+nbr_lag12"}
    model_path = os.path.join(BACKTEST_DIR, model_filename(UID, MODEL_VERSION, cfg, extra=extra))

    context_idx = y.loc[train.index.min() : test.index.max()].index
    exog_ctx = build_exog_for_uid(UID, context_idx)
    exog_train = exog_ctx.loc[train.index]
    exog_test = exog_ctx.loc[test.index]

    if os.path.exists(model_path):
        res = load_model(model_path)
        print(f"[bt] loaded cached model: {model_path}")
    else:
        start_params = None

        if USE_PROD_WARMSTART:
            prod_path = os.path.join(PROD_MODEL_DIR, model_filename(UID, MODEL_VERSION, cfg))
            if os.path.exists(prod_path):
                prev = load_model(prod_path)
                start_params = getattr(prev, "params", None)
                print(f"[bt] warm-start params from prod model: {prod_path}")
            else:
                print("[bt] prod model not found for warm-start; cold start")

        t0 = time.time()
        maxiter_first = WARM_MAXITER if start_params is not None else FALLBACK_MAXITER

        res = fit_sarimax(
            y=train,
            exog=exog_train,
            cfg=cfg,
            start_params=start_params,
            maxiter_override=maxiter_first,
        )

        converged = getattr(res, "mle_retvals", {}).get("converged", True)
        print(f"[bt] fit done maxiter={maxiter_first} converged={converged} seconds={time.time()-t0:.1f}")

        if start_params is not None and not converged and FALLBACK_MAXITER > WARM_MAXITER:
            t1 = time.time()
            print(f"[bt] warm-start did not converge, retrying maxiter={FALLBACK_MAXITER}")
            res = fit_sarimax(
                y=train,
                exog=exog_train,
                cfg=cfg,
                start_params=start_params,
                maxiter_override=FALLBACK_MAXITER,
            )
            converged2 = getattr(res, "mle_retvals", {}).get("converged", True)
            print(f"[bt] fallback fit done converged={converged2} seconds={time.time()-t1:.1f}")

        save_model(res, model_path)
        print(f"[bt] trained+cached model: {model_path}")

    yhat = res.get_forecast(steps=len(test), exog=exog_test).predicted_mean.to_numpy(dtype=float)
    p = clip01(yhat)
    y_true = test.to_numpy(dtype=int)

    _print_cls_metrics("[bt] hourly", y_true, p, HOURLY_THRESHOLDS)

    for h in (6, 24):
        y_h = horizon_labels(y_true, h)

        n = len(p)
        n_full = max(0, n - h + 1)
        risks_full = np.array([risk_any(p[i : i + h]) for i in range(n_full)], dtype=float)
        y_h_full = y_h[:n_full]

        _print_cls_metrics(f"[bt] horizon {h}h", y_h_full, risks_full, HORIZON_THRESHOLDS)

    preview = pd.DataFrame({"y": y_true[:24], "p": p[:24]}, index=test.index[:24])
    print("[bt] first 24h preview:")
    print(preview.to_string())


if __name__ == "__main__":
    main()
