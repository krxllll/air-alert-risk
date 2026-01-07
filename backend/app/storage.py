from __future__ import annotations

import os
from pathlib import Path

SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "/data/runtime/snapshots"))
HTTP_CACHE_DIR = Path(os.getenv("HTTP_CACHE_DIR", "/data/runtime/http_cache"))

SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
HTTP_CACHE_DIR.mkdir(parents=True, exist_ok=True)

BY_OBLAST_SNAPSHOT_FILE = SNAPSHOT_DIR / "iot_by_oblast.snapshot.json"
BY_OBLAST_META_KEY = "iot_by_oblast"
