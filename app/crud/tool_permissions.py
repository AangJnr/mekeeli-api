from sqlalchemy.orm import Session

from app.db import models
from app import schemas


def create_tool_permission(db: Session, permission: schemas.ToolPermissionCreate):
    db_permission = models.ToolPermission(**permission.dict())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


def get_tool_permissions(db: Session, tool_id: str):
    return db.query(models.ToolPermission).filter(models.ToolPermission.tool_id == tool_id).all()


def find_allowed_permission(db: Session, tool_id: str, conversation_id: str | None):
    query = db.query(models.ToolPermission).filter(
        models.ToolPermission.tool_id == tool_id,
        models.ToolPermission.allowed.is_(True),
    )
    global_permission = query.filter(models.ToolPermission.scope == "global").first()
    if global_permission:
        return global_permission

    if conversation_id:
        return query.filter(
            models.ToolPermission.scope.in_(["conversation", "session"]),
            models.ToolPermission.conversation_id == conversation_id,
        ).first()

    return None
