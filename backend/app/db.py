import os
import psycopg

def dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "air_alert")
    user = os.getenv("POSTGRES_USER", "air_alert")
    pwd = os.getenv("POSTGRES_PASSWORD", "air_alert")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

def get_conn():
    return psycopg.connect(dsn())

def init_db() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS alarm_events_oblast (
              id BIGSERIAL PRIMARY KEY,
              oblast_uid INT NOT NULL,
              started_at TIMESTAMPTZ NOT NULL,
              finished_at TIMESTAMPTZ,
              source TEXT,
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              UNIQUE (oblast_uid, started_at, finished_at)
            );
            """)
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_alarm_events_oblast_uid_started
            ON alarm_events_oblast (oblast_uid, started_at);
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS alarm_bins_oblast (
              oblast_uid INT NOT NULL,
              ts TIMESTAMPTZ NOT NULL,
              is_alarm SMALLINT NOT NULL,
              PRIMARY KEY (oblast_uid, ts)
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS alarm_forecasts_hourly (
              oblast_uid INT NOT NULL,
              ts TIMESTAMPTZ NOT NULL,
              p_alarm DOUBLE PRECISION NOT NULL,
              model_version TEXT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              PRIMARY KEY (oblast_uid, ts, model_version)
            );
            """)
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_alarm_forecasts_hourly_uid_ts
            ON alarm_forecasts_hourly (oblast_uid, ts);
            """)
            conn.commit()
