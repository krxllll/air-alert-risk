from __future__ import annotations

from datetime import datetime, timedelta, timezone
import psycopg

from app.db import dsn
from app.ua_oblasts import OBLASTS_ORDERED

BIN_SECONDS = 3600

def floor_to_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)

def iter_hours(start: datetime, end: datetime):
    cur = floor_to_hour(start)
    while cur < end:
        yield cur
        cur += timedelta(hours=1)

def main() -> None:
    uids = [o.uid for o in OBLASTS_ORDERED]

    with psycopg.connect(dsn()) as conn:
        with conn.cursor() as cur:
            for uid in uids:
                cur.execute(
                    "SELECT min(started_at), max(finished_at) FROM alarm_events_oblast WHERE oblast_uid=%s",
                    (uid,),
                )
                row = cur.fetchone()
                if not row or row[0] is None or row[1] is None:
                    print(f"[bins] uid={uid}: no data")
                    continue

                min_start, max_finish = row[0], row[1]
                if max_finish is None:
                    max_finish = datetime.now(timezone.utc)

                cur.execute(
                    """
                    SELECT started_at, finished_at
                    FROM alarm_events_oblast
                    WHERE oblast_uid=%s
                    ORDER BY started_at
                    """,
                    (uid,),
                )
                events = cur.fetchall()

                alarm_hours = set()
                for started_at, finished_at in events:
                    if finished_at is None:
                        continue
                    for h in iter_hours(started_at, finished_at):
                        alarm_hours.add(h)

                total = 0
                inserted = 0

                for h in iter_hours(min_start, max_finish):
                    is_alarm = 1 if h in alarm_hours else 0
                    cur.execute(
                        """
                        INSERT INTO alarm_bins_oblast (oblast_uid, ts, is_alarm)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (oblast_uid, ts) DO UPDATE SET is_alarm=EXCLUDED.is_alarm
                        """,
                        (uid, h, is_alarm),
                    )
                    total += 1
                    inserted += cur.rowcount

                conn.commit()
                print(f"[bins] uid={uid}: hours={total}")

if __name__ == "__main__":
    main()
