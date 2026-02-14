from sqlalchemy.orm import Session

from app.db import models


def create_file(db: Session, **kwargs):
    db_file = models.File(**kwargs)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_file(db: Session, file_id: str):
    return db.query(models.File).filter(models.File.id == file_id).first()


def list_files(db: Session, user_id: str):
    return db.query(models.File).filter(models.File.user_id == user_id).order_by(models.File.created_at.desc()).all()
