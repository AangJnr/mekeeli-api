
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import schemas
import models
import security
import crud.history as history_crud
from database import get_db
from services.mcp_config import get_agent_for_user

router = APIRouter()

class ChatResponse(schemas.BaseModel):
    """Chat response schema."""
    result: str
    conversation_id: int

class ChatMessage(schemas.BaseModel):
    """Chat message schema."""
    message: str
    conversation_id: int | None = None

async def stream_agent_response(db: Session, conversation_id: int, user_message: str, agent):
    """
    Streams the agent's response, yielding each chunk, and saves the full 
    response to the database after completion.
    """
    full_response = []
    # Assuming the agent has a streaming method like 'astream'
    async for chunk in agent.astream(user_message):
        full_response.append(chunk)
        yield chunk
    
    # Once streaming is complete, save the full response to the history
    history_crud.create_chat_message(
        db=db, 
        conversation_id=conversation_id, 
        sender="ai", 
        content="".join(full_response)
    )

@router.post("/chat", tags=["Chat"])
async def run_chat(
    chat_message: ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    """
    Processes a user's chat message using a dynamically configured agent, 
    maintaining conversation history and streaming the response.
    """
    # 1. Get or create the conversation
    conversation_id = chat_message.conversation_id
    if conversation_id:
        conversation = history_crud.get_conversation(db, conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Conversation not found or access denied")
    else:
        conversation = history_crud.create_conversation(db, user_id=current_user.id)
        conversation_id = conversation.id

    # 2. Add the user's new message to the history
    history_crud.create_chat_message(
        db=db, 
        conversation_id=conversation_id, 
        sender="user", 
        content=chat_message.message
    )

    # 3. Get the agent for the user
    agent = get_agent_for_user(db, current_user)

    # 4. Return a streaming response
    return StreamingResponse(
        stream_agent_response(db, conversation_id, chat_message.message, agent), 
        media_type="text/plain"
    )
