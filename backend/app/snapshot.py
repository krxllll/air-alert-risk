from __future__ import annotations

import json
import os
from typing import Any

from .storage import BY_OBLAST_SNAPSHOT_PATH


def read_by_oblast_snapshot() -> dict[str, Any] | None:
    if not os.path.exists(BY_OBLAST_SNAPSHOT_PATH):
        return None
    try:
        with open(BY_OBLAST_SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
