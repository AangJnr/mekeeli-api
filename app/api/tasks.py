from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db import models
from app import schemas
from app.core import security
from app.crud import tasks as crud_tasks
from app.db.session import get_db

router = APIRouter()


def get_owned_task(db: Session, task_id: str, current_user: models.User) -> models.Task:
    task = crud_tasks.get_task(db, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/tasks", response_model=schemas.Task, tags=["Tasks"])
def create_task(
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    try:
        return crud_tasks.create_task(db, payload, user_id=current_user.id, org_id=current_user.org_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/tasks", response_model=list[schemas.Task], tags=["Tasks"])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    return (
        db.query(models.Task)
        .filter(models.Task.user_id == current_user.id)
        .order_by(models.Task.created_at.desc())
        .all()
    )


@router.post("/tasks/{task_id}/enable", response_model=schemas.Task, tags=["Tasks"])
def enable_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    task = get_owned_task(db, task_id, current_user)
    try:
        return crud_tasks.set_task_enabled(db, task, True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/tasks/{task_id}/disable", response_model=schemas.Task, tags=["Tasks"])
def disable_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    task = get_owned_task(db, task_id, current_user)
    return crud_tasks.set_task_enabled(db, task, False)


@router.patch("/tasks/{task_id}", response_model=schemas.Task, tags=["Tasks"])
def update_task(
    task_id: str,
    updates: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    task = get_owned_task(db, task_id, current_user)
    try:
        return crud_tasks.update_task(db, task, updates)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    task = get_owned_task(db, task_id, current_user)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tasks/{task_id}/runs", response_model=list[schemas.TaskRun], tags=["Tasks"])
def list_task_runs(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    task = get_owned_task(db, task_id, current_user)
    return crud_tasks.get_task_runs(db, task.id)
