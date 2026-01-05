from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheItem:
    value: Any
    expires_at: float
    last_modified: str | None = None


class TTLCache:
    def __init__(self) -> None:
        self._data: dict[str, CacheItem] = {}

    def get(self, key: str) -> CacheItem | None:
        item = self._data.get(key)
        if not item:
            return None
        if item.expires_at <= time.time():
            return item
        return item

    @staticmethod
    def is_fresh(item: CacheItem) -> bool:
        return item.expires_at > time.time()

    def set(self, key: str, value: Any, ttl_seconds: int, last_modified: str | None = None) -> None:
        self._data[key] = CacheItem(
            value=value,
            expires_at=time.time() + ttl_seconds,
            last_modified=last_modified,
        )

    def touch(self, key: str, ttl_seconds: int) -> None:
        item = self._data.get(key)
        if not item:
            return
        item.expires_at = time.time() + ttl_seconds

    def clear(self) -> None:
        self._data.clear()


cache = TTLCache()
