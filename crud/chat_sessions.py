
from sqlalchemy.orm import Session
import models, schemas

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

def get_session_messages(db: Session, session_id: str):
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.timestamp.asc())
        .all()
    )
