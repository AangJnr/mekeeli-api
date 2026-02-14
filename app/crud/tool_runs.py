from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db import models


def create_tool_run(db: Session, tool_id: str, conversation_id: str | None, status: str, input_payload: dict | None):
    run = models.ToolRun(
        tool_id=tool_id,
        conversation_id=conversation_id,
        status=status,
        input=input_payload,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_tool_run(db: Session, run: models.ToolRun, status: str, output: dict | None = None, error: str | None = None):
    run.status = status
    run.output = output
    run.error = error
    if status in {"succeeded", "failed", "blocked"}:
        run.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def get_tool_runs(db: Session, conversation_id: str | None = None, limit: int = 20):
    query = db.query(models.ToolRun).order_by(models.ToolRun.started_at.desc())
    if conversation_id:
        query = query.filter(models.ToolRun.conversation_id == conversation_id)
    if limit:
        query = query.limit(limit)
    return query.all()
