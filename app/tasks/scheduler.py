from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import models
from app.crud import tasks as crud_tasks
from app.tasks.recurrence import compute_next_run_at
from app.tasks.runner import run_task_payload


def _update_task_after_run(db: Session, task: models.Task):
    if task.schedule_type == "once":
        task.is_active = False
        task.next_run_at = None
    else:
        task.next_run_at = compute_next_run_at(task.schedule_type, task.schedule_value, task.timezone)
        if task.next_run_at is None:
            task.is_active = False
    db.commit()


def run_scheduler_tick(db: Session):
    now = datetime.now(timezone.utc)
    # Pull all due tasks in one query so execution order is deterministic by next_run_at.
    due_tasks = (
        db.query(models.Task)
        .filter(models.Task.is_active.is_(True))
        .filter(models.Task.next_run_at.isnot(None))
        .filter(models.Task.next_run_at <= now)
        .order_by(models.Task.next_run_at.asc())
        .all()
    )

    for task in due_tasks:
        run = crud_tasks.create_task_run(db, task.id, status="running")
        try:
            output = run_task_payload(db, task)
            run.status = "succeeded"
            run.output = output
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as exc:
            run.status = "failed"
            run.logs = str(exc)
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
        finally:
            # Always reschedule/deactivate even when execution fails.
            _update_task_after_run(db, task)
