from __future__ import annotations

import os
import subprocess
import sys

DATASET_PATH = os.getenv("DATASET_PATH", "/datasets/official_data_uk.csv")


def run(cmd: list[str]) -> None:
    print("[load] running:", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> None:
    run([sys.executable, "scripts/init_db.py"])
    run([sys.executable, "scripts/ensure_dataset.py"])
    run([sys.executable, "scripts/import_events_oblast.py", DATASET_PATH])
    run([sys.executable, "scripts/build_hourly_bins.py"])
    print("[load] done")


if __name__ == "__main__":
    main()
