
from sqlalchemy.orm import Session
from app.db import models
from app import schemas
import uuid
from app.tasks.recurrence import compute_next_run_at

def get_task(db: Session, task_id: str):
    """
    Retrieves a single task by its ID.
    """
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieves a list of tasks.
    """
    return db.query(models.Task).offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate, user_id: uuid.UUID, org_id: uuid.UUID = None):
    """
    Creates a new task for a user, optionally associated with an organization.
    """
    next_run_at = compute_next_run_at(task.schedule_type, task.schedule_value, task.timezone)
    db_task = models.Task(
        **task.dict(exclude={"enabled"}),
        user_id=user_id,
        org_id=org_id,
        is_active=task.enabled,
        next_run_at=next_run_at,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task: models.Task, updates: schemas.TaskUpdate):
    update_data = updates.dict(exclude_unset=True, exclude={"enabled"})
    for key, value in update_data.items():
        setattr(task, key, value)
    if updates.enabled is not None:
        task.is_active = updates.enabled
    if "schedule_type" in update_data or "schedule_value" in update_data or "timezone" in update_data:
        task.next_run_at = compute_next_run_at(task.schedule_type, task.schedule_value, task.timezone)
    db.commit()
    db.refresh(task)
    return task

def set_task_enabled(db: Session, task: models.Task, enabled: bool):
    task.is_active = enabled
    if enabled:
        task.next_run_at = compute_next_run_at(task.schedule_type, task.schedule_value, task.timezone)
    db.commit()
    db.refresh(task)
    return task

def create_task_run(db: Session, task_id: str, status: str, logs: str | None = None, output: dict | None = None):
    run = models.TaskRun(task_id=task_id, status=status, logs=logs, output=output)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run

def get_task_runs(db: Session, task_id: str):
    return (
        db.query(models.TaskRun)
        .filter(models.TaskRun.task_id == task_id)
        .order_by(models.TaskRun.started_at.desc())
        .all()
    )
