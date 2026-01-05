from __future__ import annotations

import os
import httpx

DATASET_URL = os.getenv("DATASET_URL")
DATASET_PATH = os.getenv("DATASET_PATH", "/datasets/official_data_uk.csv")

def main() -> None:
    if os.path.exists(DATASET_PATH) and os.path.getsize(DATASET_PATH) > 0:
        print(f"[dataset] ok: {DATASET_PATH}")
        return

    if not DATASET_URL:
        raise RuntimeError("DATASET_URL is not set and dataset file is missing")

    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    print(f"[dataset] downloading: {DATASET_URL} -> {DATASET_PATH}")

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        r = client.get(DATASET_URL)
        r.raise_for_status()
        with open(DATASET_PATH, "wb") as f:
            f.write(r.content)

    print("[dataset] downloaded")

if __name__ == "__main__":
    main()
