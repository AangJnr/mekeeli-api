from sqlalchemy.orm import Session

from app.db import models
from app import schemas
from app.enums import SenderType
from app.crud import chat_sessions as crud_chat
from app.crud import tool_runs as crud_tool_runs
from app.crud import tools as crud_tools


def run_task_payload(db: Session, task: models.Task):
    payload = task.payload or {}
    payload_type = payload.get("type")

    if payload_type == "post_message":
        conversation_id = payload.get("conversation_id")
        content = payload.get("content")
        if not conversation_id or not content:
            return {"status": "skipped", "reason": "Missing conversation_id or content"}
        session = crud_chat.get_chat_session(db, conversation_id)
        if not session:
            return {"status": "skipped", "reason": "Conversation not found"}
        crud_chat.create_chat_message(
            db,
            schemas.ChatMessageCreate(sender=SenderType.AI, content=content),
            conversation_id,
        )
        return {"status": "posted", "conversation_id": conversation_id}

    if payload_type == "tool_run":
        tool_id = payload.get("tool_id")
        parameters = payload.get("parameters", {})
        if not tool_id:
            return {"status": "skipped", "reason": "Missing tool_id"}
        tool = crud_tools.get_tool(db, tool_id)
        if not tool:
            return {"status": "skipped", "reason": "Tool not found"}
        run = crud_tool_runs.create_tool_run(
            db,
            tool_id=tool.id,
            conversation_id=payload.get("conversation_id"),
            status="queued",
            input_payload=parameters,
        )
        return {"status": "queued", "run_id": run.id}

    return {"status": "noop"}
