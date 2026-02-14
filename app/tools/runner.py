from sqlalchemy.orm import Session

from app.api import tool_runner as tool_runner_api
from app.db import models


def run_tool(
    tool_execution: tool_runner_api.ToolExecution,
    db: Session,
    current_user: models.User,
):
    return tool_runner_api.run_tool(
        tool_execution=tool_execution,
        db=db,
        current_user=current_user,
    )


def list_tool_runs(conversation_id: str | None, limit: int, db: Session):
    return tool_runner_api.list_tool_runs(
        conversation_id=conversation_id,
        limit=limit,
        db=db,
    )


def test_tool(tool_id: str, db: Session):
    return tool_runner_api.test_tool(tool_id=tool_id, db=db)
