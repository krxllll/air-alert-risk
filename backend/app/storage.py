import os

SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "/data")
BY_OBLAST_SNAPSHOT_PATH = os.path.join(SNAPSHOT_DIR, "by_oblast_snapshot.json")
BY_OBLAST_LAST_MODIFIED_PATH = os.path.join(SNAPSHOT_DIR, "by_oblast_last_modified.txt")
