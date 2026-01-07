from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

from statsmodels.tsa.statespace.sarimax import SARIMAXResults

from .sarimax_core import SarimaxConfig


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def model_filename(
    uid: int,
    model_version: str,
    cfg: SarimaxConfig,
    extra: dict[str, Any] | None = None,
) -> str:
    payload: dict[str, Any] = {"uid": uid, "model_version": model_version, "cfg": asdict(cfg)}
    if extra:
        payload["extra"] = extra
    h = _stable_hash(payload)
    return f"sarimax_uid{uid}_{model_version}_{h}.pkl"


def _gzip_file(src: Path, dst_gz: Path, level: int = 9) -> None:
    tmp = dst_gz.with_suffix(dst_gz.suffix + ".tmp")
    with open(src, "rb") as f_in, gzip.open(tmp, "wb", compresslevel=level) as f_out:
        shutil.copyfileobj(f_in, f_out)
    tmp.replace(dst_gz)


def save_model(res: SARIMAXResults, path: str) -> None:
    out = Path(path)
    ensure_dir(str(out.parent))

    res.save(str(out))

    if os.getenv("GZIP_MODELS", "0") not in ("1", "true", "True"):
        return

    level = int(os.getenv("GZIP_LEVEL", "9"))
    dst_gz = Path(str(out) + ".gz")
    _gzip_file(out, dst_gz, level=level)

    if os.getenv("DELETE_PKL", "0") in ("1", "true", "True"):
        try:
            out.unlink()
        except Exception:
            pass


def load_model(path: str) -> SARIMAXResults:
    p = Path(path)
    if p.exists():
        return SARIMAXResults.load(str(p))

    gz = Path(str(p) + ".gz")
    if not gz.exists():
        raise FileNotFoundError(f"Model not found: {p} or {gz}")

    with gzip.open(gz, "rb") as f:
        return SARIMAXResults.load(f)
