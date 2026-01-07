from __future__ import annotations

import os
import gzip
import shutil
from pathlib import Path

MODEL_DIR = Path(os.getenv("MODEL_DIR", "/data/models/sarimax"))
REMOVE_ORIGINAL = os.getenv("REMOVE_ORIGINAL", "0") == "1"


def main() -> None:
    if not MODEL_DIR.exists():
        raise RuntimeError(f"MODEL_DIR does not exist: {MODEL_DIR}")

    pkl_files = sorted(MODEL_DIR.glob("*.pkl"))

    if not pkl_files:
        print("[compact] no .pkl models found")
        return

    print(f"[compact] found {len(pkl_files)} model(s)")

    for pkl_path in pkl_files:
        gz_path = pkl_path.with_suffix(pkl_path.suffix + ".gz")

        if gz_path.exists():
            print(f"[compact] skip (already gz): {gz_path.name}")
            continue

        print(f"[compact] compressing {pkl_path.name} -> {gz_path.name}")

        with open(pkl_path, "rb") as f_in, gzip.open(gz_path, "wb", compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)

        orig_size = pkl_path.stat().st_size
        gz_size = gz_path.stat().st_size
        ratio = gz_size / orig_size if orig_size else 0.0

        print(
            f"[compact] done: "
            f"orig={orig_size/1024/1024:.1f}MB "
            f"gz={gz_size/1024/1024:.1f}MB "
            f"ratio={ratio:.2f}"
        )

        if REMOVE_ORIGINAL:
            pkl_path.unlink()
            print(f"[compact] removed original: {pkl_path.name}")

    print("[compact] finished")


if __name__ == "__main__":
    main()
