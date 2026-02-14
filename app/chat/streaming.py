from app.enums import SenderType
from app import schemas
from app.crud import chat_sessions as crud_chat


async def stream_llm_response(db, session_id: str, llm, history: list, prompt: str):
    full_response = ""
    async for chunk in llm.astream(history):
        content = chunk.content
        full_response += content
        yield content

    crud_chat.create_chat_message(
        db,
        schemas.ChatMessageCreate(sender=SenderType.AI, content=full_response),
        session_id,
    )


async def stream_text_chunks(text: str):
    yield text
