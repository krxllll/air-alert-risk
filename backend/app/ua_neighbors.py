from __future__ import annotations

NEIGHBORS: dict[int, list[int]] = {
    14: [31, 10, 25, 24, 19, 4],
}

def neighbors_for(uid: int) -> list[int]:
    return NEIGHBORS.get(uid, [])
