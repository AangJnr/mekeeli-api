from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.db import models
from app.core import security
from app.crud import settings as crud_settings
from app.crud import tools as crud_tools
from app.crud import tool_runs as crud_tool_runs
from app.crud import mcp_servers as crud_mcp
from app.db.session import get_db

router = APIRouter()


@router.get("/settings", response_model=schemas.Settings, tags=["Settings"])
def get_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    return crud_settings.get_settings(db)


@router.post("/settings", response_model=schemas.Settings, tags=["Settings"])
def update_settings(
    updates: schemas.SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    settings = crud_settings.get_settings(db)
    return crud_settings.update_settings(db, settings, updates)


def _list_ollama_models() -> list[str]:
    try:
        import ollama
    except Exception:
        return []

    try:
        response = ollama.list()
        return [model.get("name") for model in response.get("models", [])]
    except Exception:
        return []


@router.get("/settings/diagnostics", response_model=schemas.Diagnostics, tags=["Settings"])
def diagnostics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    settings = crud_settings.get_settings(db)
    tools = crud_tools.get_tools(db)
    enabled_tools = [
        {
            "id": tool.id,
            "name": tool.name,
            "requires_network": tool.requires_network,
            "enabled": tool.enabled,
        }
        for tool in tools
        if tool.enabled
    ]
    mcp_servers = crud_mcp.get_mcp_servers(db)
    external_endpoints = [server.url for server in mcp_servers if server.url]
    recent_runs = crud_tool_runs.get_tool_runs(db, limit=10)
    recent_tool_runs: list[dict[str, Any]] = []
    for run in recent_runs:
        recent_tool_runs.append(
            {
                "id": run.id,
                "tool_id": run.tool_id,
                "conversation_id": run.conversation_id,
                "status": run.status,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "error": run.error,
            }
        )

    return schemas.Diagnostics(
        offline_mode=settings.offline_mode,
        external_endpoints=external_endpoints,
        enabled_tools=enabled_tools,
        ollama_models=_list_ollama_models(),
        recent_tool_runs=recent_tool_runs,
    )
