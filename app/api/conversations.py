from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db import models
from app import schemas
from app.core import security
from app.crud import chat_sessions as crud_chat
from app.db.session import get_db

router = APIRouter()


def get_owned_session(db: Session, conversation_id: str, current_user: models.User) -> models.ChatSession:
    session = crud_chat.get_chat_session(db, conversation_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return session


@router.get("/conversations", response_model=list[schemas.ChatSessionSummary], tags=["Conversations"])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    return crud_chat.get_user_chat_sessions(db, current_user.id)


@router.post("/conversations", response_model=schemas.ChatSessionSummary, tags=["Conversations"])
def create_conversation(
    payload: schemas.ChatSessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    session = crud_chat.create_chat_session(
        db,
        schemas.ChatSessionCreate(
            user_id=current_user.id,
            title=payload.title,
        ),
    )
    return session


@router.get("/conversations/{conversation_id}", response_model=schemas.ChatSessionSummary, tags=["Conversations"])
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    return get_owned_session(db, conversation_id, current_user)


@router.patch("/conversations/{conversation_id}", response_model=schemas.ChatSessionSummary, tags=["Conversations"])
def update_conversation(
    conversation_id: str,
    updates: schemas.ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    session = get_owned_session(db, conversation_id, current_user)
    return crud_chat.update_chat_session(db, session, updates)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Conversations"])
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    session = get_owned_session(db, conversation_id, current_user)
    crud_chat.delete_chat_session(db, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/conversations/{conversation_id}/messages", response_model=list[schemas.ChatMessage], tags=["Conversations"])
def list_messages(
    conversation_id: str,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    session = get_owned_session(db, conversation_id, current_user)
    return crud_chat.get_session_messages(db, session.id, limit=limit, cursor=cursor)
