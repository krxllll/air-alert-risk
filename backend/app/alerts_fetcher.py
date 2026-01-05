from __future__ import annotations

import httpx
from .settings import settings
from .cache import cache
from .alerts_meta import read_last_modified, write_last_modified

TIMEOUT = 10.0

def _auth_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    if not settings.alerts_token:
        raise RuntimeError("ALERTS_API_TOKEN is not set")
    h = {"Authorization": f"Bearer {settings.alerts_token}"}
    if extra:
        h.update(extra)
    return h


async def fetch_json(
    *,
    key: str,
    path: str,
    ttl_seconds: int,
    params: dict | None = None,
) -> dict:
    cached = cache.get(key)
    if cached and cache.is_fresh(cached):
        return cached.value

    last_modified = cached.last_modified if cached else None
    if not last_modified:
        last_modified = read_last_modified(key)

    extra_headers = {}
    if last_modified:
        extra_headers["If-Modified-Since"] = last_modified

    url = f"{settings.alerts_base_url}{path}"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(url, headers=_auth_headers(extra_headers), params=params)
        lm = r.headers.get("Last-Modified")

        if r.status_code == 304:
            if not cached:
                r2 = await client.get(url, headers=_auth_headers(), params=params)
                r2.raise_for_status()
                lm2 = r2.headers.get("Last-Modified")
                data2 = r2.json()
                cache.set(key, data2, ttl_seconds=ttl_seconds, last_modified=lm2)
                if lm2:
                    write_last_modified(key, lm2)
                return data2

            cache.touch(key, ttl_seconds=ttl_seconds)
            return cached.value

        r.raise_for_status()
        data = r.json()

        cache.set(key, data, ttl_seconds=ttl_seconds, last_modified=lm)
        if lm:
            write_last_modified(key, lm)
        return data
