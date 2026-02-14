import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from app.db.session import SessionLocal
from app.tasks.scheduler import run_scheduler_tick
from app.rag.worker import run_ingestion_tick


def run_worker():
    poll_interval = int(os.getenv("WORKER_POLL_INTERVAL", "10"))
    heartbeat_path = Path(os.getenv("WORKER_HEARTBEAT_PATH", "data/worker_heartbeat.json"))
    heartbeat_path.parent.mkdir(parents=True, exist_ok=True)

    while True:
        db = SessionLocal()
        try:
            # Run both schedulers in one DB session so worker heartbeat reflects a full tick.
            run_scheduler_tick(db)
            run_ingestion_tick(db)
            heartbeat_path.write_text(
                json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()}),
                encoding="utf-8",
            )
        finally:
            db.close()
        time.sleep(poll_interval)


if __name__ == "__main__":
    run_worker()
