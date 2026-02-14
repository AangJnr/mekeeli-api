from sqlalchemy.orm import Session

from app.db import models


def list_enabled_tools(db: Session) -> list[models.Tool]:
    return db.query(models.Tool).filter(models.Tool.enabled.is_(True)).all()


def get_tool_by_name(db: Session, name: str):
    return db.query(models.Tool).filter(models.Tool.name == name).first()
