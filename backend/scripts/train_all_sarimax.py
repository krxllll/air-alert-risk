from __future__ import annotations

import os
import sys
import time

from app.ua_oblasts import OBLASTS_ORDERED
from app.ml.sarimax_core import SarimaxConfig, fit_sarimax
from app.ml.model_store import ensure_dir, load_model, save_model, model_filename

from app.data_access.bins import load_bins_series
from app.data_access.exog import build_exog_for_uid


MODEL_VERSION = os.getenv("MODEL_VERSION", "sarimax_v1_hourly")
MODEL_DIR = os.getenv("MODEL_DIR", "/data/models/sarimax")

WARM_MAXITER = int(os.getenv("WARM_MAXITER", "120"))
FALLBACK_MAXITER = int(os.getenv("FALLBACK_MAXITER", "200"))

MIN_BINS = int(os.getenv("MIN_TRAIN_BINS", str(24 * 30)))


def _is_converged(res) -> bool:
    try:
        return bool(getattr(res, "mle_retvals", {}).get("converged", True))
    except Exception:
        return True


def main() -> int:
    cfg = SarimaxConfig()
    ensure_dir(MODEL_DIR)

    ok = 0
    skipped = 0
    errors = 0

    for o in OBLASTS_ORDERED:
        uid = o.uid

        try:
            y = load_bins_series(uid)
        except RuntimeError as e:
            msg = str(e).lower()
            if "no bins" in msg:
                print(f"[train-all] uid={uid} skip: no bins")
                skipped += 1
                continue
            print(f"[train-all] uid={uid} error: {e}")
            errors += 1
            continue
        except Exception as e:
            print(f"[train-all] uid={uid} error: {e}")
            errors += 1
            continue

        if len(y) < MIN_BINS:
            print(f"[train-all] uid={uid} skip: not enough data n={len(y)}")
            skipped += 1
            continue

        exog = build_exog_for_uid(uid, y.index)

        path = os.path.join(MODEL_DIR, model_filename(uid, MODEL_VERSION, cfg))
        start_params = None

        if os.path.exists(path):
            try:
                prev = load_model(path)
                start_params = getattr(prev, "params", None)
            except Exception as e:
                print(f"[train-all] uid={uid} warn: failed to load prev model ({e}); training cold")

        t0 = time.time()
        try:
            first_maxiter = WARM_MAXITER if start_params is not None else FALLBACK_MAXITER

            res = fit_sarimax(
                y=y,
                exog=exog,
                cfg=cfg,
                start_params=start_params,
                maxiter_override=first_maxiter,
            )

            converged = _is_converged(res)

            if start_params is not None and (not converged) and FALLBACK_MAXITER > WARM_MAXITER:
                res = fit_sarimax(
                    y=y,
                    exog=exog,
                    cfg=cfg,
                    start_params=start_params,
                    maxiter_override=FALLBACK_MAXITER,
                )
                converged = _is_converged(res)

            save_model(res, path)
            print(f"[train-all] uid={uid} converged={converged} seconds={time.time()-t0:.1f} saved={path}")
            ok += 1

        except Exception as e:
            print(f"[train-all] uid={uid} error during fit: {e}")
            errors += 1
            continue

    print(f"[train-all] done ok={ok} skipped={skipped} errors={errors}")

    return 0 if ok > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
