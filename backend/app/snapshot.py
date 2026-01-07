from __future__ import annotations

import json
from typing import Any

from .storage import BY_OBLAST_SNAPSHOT_FILE

def read_by_oblast_snapshot() -> dict[str, Any] | None:
    if not BY_OBLAST_SNAPSHOT_FILE.exists():
        return None
    return json.loads(BY_OBLAST_SNAPSHOT_FILE.read_text(encoding="utf-8"))
