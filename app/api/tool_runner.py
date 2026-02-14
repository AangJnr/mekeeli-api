
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from jsonschema import validate as jsonschema_validate
from jsonschema import ValidationError

from app import schemas
from app.db import models
from app.core import security
from app.crud import tools as crud_tools
from app.crud import chat_sessions as crud_chat
from app.crud import tool_permissions as crud_tool_permissions
from app.crud import tool_runs as crud_tool_runs
from app.crud import settings as crud_settings
from app.db.session import get_db

router = APIRouter()

class ToolExecution(BaseModel):
    tool_id: str | None = None
    tool_name: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict, alias="arguments")
    conversation_id: str | None = None
    confirm: bool = False
    reason: str | None = None

    class Config:
        allow_population_by_field_name = True

@router.post("/tools/run", dependencies=[Depends(security.get_current_active_user)])
def run_tool(
    tool_execution: ToolExecution,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    if not tool_execution.tool_id and not tool_execution.tool_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tool ID or name is required")

    tool = None
    if tool_execution.tool_id:
        tool = crud_tools.get_tool(db, tool_id=tool_execution.tool_id)
    elif tool_execution.tool_name:
        tool = db.query(models.Tool).filter(models.Tool.name == tool_execution.tool_name).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    conversation_id = tool_execution.conversation_id
    if conversation_id:
        session = crud_chat.get_chat_session(db, conversation_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    run = crud_tool_runs.create_tool_run(
        db,
        tool_id=tool.id,
        conversation_id=conversation_id,
        status="running",
        input_payload=tool_execution.parameters,
    )

    settings = crud_settings.get_settings(db)
    # Guardrails are enforced before script execution to ensure blocked attempts are still audited.
    if not tool.enabled:
        crud_tool_runs.update_tool_run(db, run, status="blocked", error="Tool is disabled")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tool is disabled")

    if settings.offline_mode and tool.requires_network:
        crud_tool_runs.update_tool_run(db, run, status="blocked", error="Tool requires network while offline")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tool requires network while offline")

    permission = crud_tool_permissions.find_allowed_permission(
        db,
        tool_id=tool.id,
        conversation_id=conversation_id,
    )
    if not permission:
        crud_tool_runs.update_tool_run(db, run, status="blocked", error="Tool permission not granted")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tool permission not granted")

    if tool.danger_level == "high" and not tool_execution.confirm:
        crud_tool_runs.update_tool_run(db, run, status="blocked", error="Tool requires confirmation")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tool requires confirmation")

    try:
        if tool.input_schema:
            try:
                jsonschema_validate(instance=tool_execution.parameters, schema=tool.input_schema)
            except ValidationError as exc:
                crud_tool_runs.update_tool_run(db, run, status="failed", error=f"Input schema validation failed: {exc.message}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input schema validation failed")

        tool_config = tool.config or {}
        script = tool_config.get("script")
        entrypoint = tool_config.get("entrypoint", "run")
        if not script:
            raise ValueError("Tool config is missing 'script'")

        exec_globals: dict[str, Any] = {}
        # Tool scripts are dynamically loaded from DB config and must expose the configured entrypoint.
        exec(script, exec_globals)
        if entrypoint not in exec_globals:
            raise ValueError(f"Tool entrypoint '{entrypoint}' not found")

        result = exec_globals[entrypoint](tool_execution.parameters)
        if tool.output_schema:
            try:
                jsonschema_validate(instance=result, schema=tool.output_schema)
            except ValidationError as exc:
                crud_tool_runs.update_tool_run(db, run, status="failed", error=f"Output schema validation failed: {exc.message}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Output schema validation failed")
        crud_tool_runs.update_tool_run(db, run, status="succeeded", output={"result": result})
        return {"result": result, "run_id": run.id}
    except Exception as e:
        crud_tool_runs.update_tool_run(db, run, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error executing tool: {e}")

@router.get("/tool-runs", response_model=list[schemas.ToolRun], dependencies=[Depends(security.get_current_active_user)])
def list_tool_runs(
    conversation_id: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return crud_tool_runs.get_tool_runs(db, conversation_id=conversation_id, limit=limit)

@router.post("/tools/{tool_id}/test", dependencies=[Depends(security.get_current_admin_user)])
def test_tool(
    tool_id: str,
    db: Session = Depends(get_db),
):
    tool = crud_tools.get_tool(db, tool_id=tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool_config = tool.config or {}
    if not tool_config.get("script"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tool config missing 'script'")
    return {"status": "ok"}
