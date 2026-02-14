from datetime import datetime, timezone
import json
import os
from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter()


def _check_db() -> dict:
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _check_ollama() -> dict:
    try:
        import ollama  # type: ignore
    except Exception as exc:
        return {"status": "unavailable", "detail": str(exc)}

    try:
        ollama.list()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _check_worker() -> dict:
    heartbeat_path = Path(os.getenv("WORKER_HEARTBEAT_PATH", "data/worker_heartbeat.json"))
    if not heartbeat_path.exists():
        return {"status": "missing"}

    try:
        payload = json.loads(heartbeat_path.read_text())
        timestamp = payload.get("timestamp")
        if not timestamp:
            return {"status": "invalid"}
        last_seen = datetime.fromisoformat(timestamp)
        now = datetime.now(timezone.utc)
        poll_interval = int(os.getenv("WORKER_POLL_INTERVAL", "10"))
        max_age = max(30, poll_interval * 3)
        age_seconds = (now - last_seen).total_seconds()
        if age_seconds <= max_age:
            return {"status": "ok", "age_seconds": age_seconds}
        return {"status": "stale", "age_seconds": age_seconds}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get("/health", tags=["Health"])
def health_check():
    db_status = _check_db()
    ollama_status = _check_ollama()
    worker_status = _check_worker()
    overall = "ok"
    if db_status["status"] != "ok":
        overall = "degraded"
    if ollama_status["status"] not in {"ok", "unavailable"}:
        overall = "degraded"
    if worker_status["status"] in {"stale", "missing", "error", "invalid"}:
        overall = "degraded"
    return {
        "status": overall,
        "db": db_status,
        "ollama": ollama_status,
        "worker": worker_status,
    }
