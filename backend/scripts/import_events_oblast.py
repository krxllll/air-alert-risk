from __future__ import annotations

import csv
import sys
from datetime import datetime
import psycopg

from app.db import dsn
from app.ua_oblasts import OBLASTS_ORDERED

NAME_TO_UID = {o.name: o.uid for o in OBLASTS_ORDERED}

def parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)

def main(csv_path: str) -> None:
    inserted = 0
    skipped = 0

    with psycopg.connect(dsn()) as conn:
        with conn.cursor() as cur:
            with open(csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("level") != "oblast":
                        continue

                    oblast_name = row.get("oblast")
                    if not oblast_name:
                        skipped += 1
                        continue

                    uid = NAME_TO_UID.get(oblast_name)
                    if uid is None:
                        raise RuntimeError(f"Unknown oblast name: {oblast_name!r}")

                    started_at = parse_dt(row["started_at"])
                    finished_at = parse_dt(row["finished_at"]) if row.get("finished_at") else None
                    source = row.get("source")

                    cur.execute(
                        """
                        INSERT INTO alarm_events_oblast (oblast_uid, started_at, finished_at, source)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (oblast_uid, started_at, finished_at) DO NOTHING
                        """,
                        (uid, started_at, finished_at, source),
                    )
                    inserted += cur.rowcount

            conn.commit()

    print(f"Inserted: {inserted}, skipped: {skipped}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_events_oblast.py path/to/dataset.csv")
        raise SystemExit(2)
    main(sys.argv[1])
