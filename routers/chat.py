
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import schemas
import models
import security
from crud import chat_sessions as crud_chat
from crud import tasks as crud_tasks
from database import get_db
from services.mcp_config import get_agent_for_user
import uuid
from enums import SenderType

router = APIRouter()

async def stream_agent_response(db: Session, session_id: uuid.UUID, prompt: str, agent, attachments: list = []):
    full_response = []
    async for chunk in agent.astream(prompt):
        full_response.append(chunk)
        yield chunk

    crud_chat.create_chat_message(
        db=db,
        session_id=session_id,
        message=schemas.ChatMessageCreate(
            sender=SenderType.AI,
            content="".join(full_response)
        )
    )

@router.post("/chat", tags=["Chat"])
async def run_chat(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    session_id = request.session_.id
    prompt = request.message

    agent = get_agent_for_user(
        db,
        current_user,
        task_id=request.task_id,
        tool_id=request.tool_id
    )

    if request.task_id:
        task = crud_tasks.get_task(db, request.task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        if task.default_prompt:
            prompt = f"{task.default_prompt}\n\nUser query: {prompt}"

    if session_id:
        session = crud_chat.get_chat_session(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat session not found or access denied")
    else:
        session = crud_chat.create_chat_session(
            db,
            schemas.ChatSessionCreate(user_id=current_user.id, task_id=request.task_id)
        )
        session_id = session.id

    message_meta_data = {
        "attachments": [att.dict() for att in request.attachments],
        "task_id": request.task_id,
        "tool_id": request.tool_id
    }
    crud_chat.create_chat_message(
        db=db,
        session_id=session_id,
        message=schemas.ChatMessageCreate(
            sender=SenderType.USER,
            content=prompt,
            metadata=message_meta_data
        )
    )

    if request.stream:
        return StreamingResponse(
            stream_agent_response(db, session_id, prompt, agent, request.attachments),
            media_type="text/plain"
        )
    else:
        result = await agent.run(prompt)
        crud_chat.create_chat_message(
            db=db,
            session_id=session_id,
            message=schemas.ChatMessageCreate(sender=SenderType.AI, content=result)
        )
        return {"result": result, "session_id": session_id}
