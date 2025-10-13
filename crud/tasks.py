
from sqlalchemy.orm import Session
import models, schemas
import uuid

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
    db_task = models.Task(
        **task.dict(),
        user_id=user_id,
        org_id=org_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task
