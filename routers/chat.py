
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage
import uuid

import schemas
import models
import security
from crud import chat_sessions as crud_chat
from crud import tasks as crud_tasks
from database import get_db
from services.mcp_config import get_agent_for_user
from services.llm_service import get_base_llm
from enums import SenderType

router = APIRouter()

async def stream_simple_response(db: Session, session_id: uuid.UUID, history: list, llm, prompt: str):
    """Streams a response from a base LLM and saves the result."""
    full_response = ""
    async for chunk in llm.astream(history + [HumanMessage(content=prompt)]):
        content = chunk.content
        full_response += content
        yield content
    
    crud_chat.create_chat_message(db, schemas.ChatMessageCreate(sender=SenderType.AI, content=full_response), session_id)

async def stream_agent_response(db: Session, session_id: uuid.UUID, agent, prompt: str):
    """Streams a response from the MCPAgent and saves the result."""
    full_response = ""
    async for chunk in agent.astream(prompt):
        full_response += chunk
        yield chunk

    crud_chat.create_chat_message(db, schemas.ChatMessageCreate(sender=SenderType.AI, content=full_response), session_id)


@router.post("/chat", tags=["Chat"])
async def run_chat(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    session_id = request.session_id
    prompt = request.message

    # --- 1. Determine if this is a simple or agent-based chat ---
    is_agent_chat = bool(request.task_id or request.tool_id or request.attachments)

    # --- 2. Get or Create Chat Session & History ---
    if session_id:
        session = crud_chat.get_chat_session(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat session not found")
        
        db_messages = crud_chat.get_session_messages(db, session_id)
        history = [
            HumanMessage(content=msg.content) if msg.sender == SenderType.USER else AIMessage(content=msg.content)
            for msg in db_messages
        ]
    else:
        session = crud_chat.create_chat_session(db, schemas.ChatSessionCreate(user_id=current_user.id, task_id=request.task_id))
        session_id = session.id
        history = []

    # --- 3. Store User Message ---
    # (This logic is now common to both paths)
    crud_chat.create_chat_message(
        db, 
        schemas.ChatMessageCreate(
            sender=SenderType.USER, 
            content=prompt,
            metadata={"attachments": [att.dict() for att in request.attachments]}
        ),
        session_id
    )

    # --- 4. Execute Logic and Get Response ---
    if is_agent_chat:
        # --- AGENT LOGIC ---
        agent = get_agent_for_user(db, current_user, task_id=request.task_id, tool_id=request.tool_id)
        
        if request.stream:
            return StreamingResponse(stream_agent_response(db, session_id, agent, prompt), media_type="text/plain")
        else:
            result = await agent.run(prompt)  
            crud_chat.create_chat_message(db, schemas.ChatMessageCreate(sender=SenderType.AI, content=result), session_id)
            return {"result": result, "session_id": str(session_id)}
    else:
        # --- SIMPLE CHAT LOGIC ---
        llm = get_base_llm(db, current_user)
        
        if request.stream:
            return StreamingResponse(stream_simple_response(db, session_id, history, llm, prompt), media_type="text/plain")
        else:
            result = await llm.ainvoke(history + [HumanMessage(content=prompt)])
            content = result.content
            crud_chat.create_chat_message(db, schemas.ChatMessageCreate(sender=SenderType.AI, content=content), session_id)
            return {"result": content, "session_id": str(session_id)}
