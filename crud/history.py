
from sqlalchemy.orm import Session
import models

def create_conversation(db: Session, user_id: int):
    db_conversation = models.Conversation(user_id=user_id)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def create_chat_message(db: Session, conversation_id: int, sender: str, content: str):
    db_message = models.ChatMessage(
        conversation_id=conversation_id, sender=sender, content=content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_conversation(db: Session, conversation_id: int):
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )

def get_user_conversations(db: Session, user_id: int):
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == user_id)
        .order_by(models.Conversation.created_at.desc())
        .all()
    )

def get_conversation_messages(db: Session, conversation_id: int):
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.conversation_id == conversation_id)
        .order_by(models.ChatMessage.timestamp.asc())
        .all()
    )
