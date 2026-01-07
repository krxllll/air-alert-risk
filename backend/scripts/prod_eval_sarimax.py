from __future__ import annotations

import os

import numpy as np
import pandas as pd

from app.data_access.bins import load_bins_series
from app.data_access.exog import build_exog_for_uid
from app.ml.metrics import (
    roc_auc,
    average_precision,
    brier,
    logloss,
    precision_recall_f1,
    confusion,
    clip01,
    risk_any,
    horizon_labels,
)
from app.ml.model_store import load_model, model_filename
from app.ml.sarimax_core import SarimaxConfig


UID = int(os.getenv("EVAL_UID", "14"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "sarimax_v1_hourly")
MODEL_DIR = os.getenv("MODEL_DIR", "/data/models/sarimax")

EVAL_DAYS = int(os.getenv("EVAL_DAYS", "60"))

LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "0"))

HOURLY_THRESHOLDS = tuple(
    float(x.strip())
    for x in os.getenv("EVAL_HOURLY_THRESHOLDS", "0.25,0.35,0.5").split(",")
    if x.strip()
)

HORIZON_THRESHOLDS = tuple(
    float(x.strip())
    for x in os.getenv("EVAL_HORIZON_THRESHOLDS", "0.4,0.55").split(",")
    if x.strip()
)


def _print_cls(prefix: str, y_true: np.ndarray, p: np.ndarray, thresholds: tuple[float, ...]) -> None:
    print(
        f"{prefix}: "
        f"AUC={roc_auc(y_true, p):.4f} "
        f"AP={average_precision(y_true, p):.4f} "
        f"Brier={brier(y_true, p):.4f} "
        f"LogLoss={logloss(y_true, p):.4f} "
        f"pos_rate={float(np.mean(y_true)):.4f}"
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
    cfg = SarimaxConfig()

    extra = {"lookback_days": LOOKBACK_DAYS} if LOOKBACK_DAYS > 0 else None
    model_path = os.path.join(MODEL_DIR, model_filename(UID, MODEL_VERSION, cfg, extra=extra))

    try:
        res = load_model(model_path)
    except FileNotFoundError:
        raise RuntimeError(
            f"Model not found: {model_path} or {model_path}.gz. "
            f"Train first (train_sarimax.py)."
        )

    y = load_bins_series(UID)
    if len(y) < (EVAL_DAYS * 24 + 24):
        raise RuntimeError("Not enough data for eval window")

    eval_end = y.index.max()
    eval_start = eval_end - pd.Timedelta(days=EVAL_DAYS) + pd.Timedelta(hours=1)
    y_eval = y.loc[eval_start:eval_end]

    context_idx = y.loc[:eval_end].index
    exog_ctx = build_exog_for_uid(UID, context_idx)
    exog_eval = exog_ctx.loc[y_eval.index]

    fc = res.get_forecast(steps=len(y_eval), exog=exog_eval)
    yhat = fc.predicted_mean.to_numpy(dtype=float)

    p = clip01(yhat)
    y_true = y_eval.to_numpy(dtype=int)

    print(f"[prod-eval] uid={UID} model_version={MODEL_VERSION} lookback_days={LOOKBACK_DAYS}")
    print(f"[prod-eval] window: {y_eval.index.min().isoformat()} .. {y_eval.index.max().isoformat()} n={len(y_eval)}")

    _print_cls("[prod-eval] hourly", y_true, p, HOURLY_THRESHOLDS)

    for h in (6, 24, 168):
        n = len(p)
        n_full = max(0, n - h + 1)

        if n_full < 50:
            print(f"[prod-eval] horizon {h}h skipped (not enough windows): n_full={n_full}")
            continue

        y_h = horizon_labels(y_true, h)[:n_full]
        risks = np.array([risk_any(p[i : i + h]) for i in range(n_full)], dtype=float)

        pos_rate = float(np.mean(y_h))

        expected_alarm_hours_mean = float(np.mean([np.sum(p[i : i + h]) for i in range(n_full)]))
        print(f"[prod-eval] horizon {h}h expected_alarm_hours(mean)={expected_alarm_hours_mean:.2f}")

        if pos_rate == 0.0 or pos_rate == 1.0:
            print(f"[prod-eval] horizon {h}h: pos_rate={pos_rate:.4f} — classification metrics skipped")
            continue

        _print_cls(f"[prod-eval] horizon {h}h", y_h, risks, HORIZON_THRESHOLDS)

    preview = pd.DataFrame({"y": y_true[:24], "p": p[:24]}, index=y_eval.index[:24])
    print("[prod-eval] first 24h preview:")
    print(preview.to_string())


if __name__ == "__main__":
    main()
