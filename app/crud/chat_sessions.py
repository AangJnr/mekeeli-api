
from sqlalchemy.orm import Session
from typing import Optional
from app.db import models
from app import schemas

def create_chat_session(db: Session, session: schemas.ChatSessionCreate):
    db_session = models.ChatSession(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def create_chat_message(db: Session, message: schemas.ChatMessageCreate, session_id: str):
    db_message = models.ChatMessage(**message.dict(), session_id=session_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_session(db: Session, session_id: str):
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id)
        .first()
    )

def get_user_chat_sessions(db: Session, user_id: str):
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == user_id)
        .order_by(models.ChatSession.created_at.desc())
        .all()
    )

def get_session_messages(db: Session, session_id: str, limit: Optional[int] = None, cursor: Optional[str] = None):
    query = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
    )

    if cursor:
        cursor_message = (
            db.query(models.ChatMessage)
            .filter(models.ChatMessage.id == cursor)
            .first()
        )
        if cursor_message:
            query = query.filter(models.ChatMessage.created_at < cursor_message.created_at)

    query = query.order_by(models.ChatMessage.created_at.asc())

    if limit:
        query = query.limit(limit)

    return query.all()

def update_chat_session(db: Session, session: models.ChatSession, updates: schemas.ChatSessionUpdate):
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session

def delete_chat_session(db: Session, session: models.ChatSession):
    db.delete(session)
    db.commit()
