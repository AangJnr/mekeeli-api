
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app import schemas
from app.db import models
from app.core import security
from app.db.session import get_db
from app.celery_worker import query_mcp_task
from app.tools.mcp_integration import get_mcp_api_key
from app.crud import mcp_servers as crud_mcp
from app.crud import settings as crud_settings

router = APIRouter()

class McpQuery(BaseModel):
    mcp_server_id: str
    query: str

@router.post("/mcp/query", status_code=202)
def query_mcp(
    query: McpQuery,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    settings = crud_settings.get_settings(db)
    if settings.offline_mode:
        raise HTTPException(status_code=403, detail="Offline mode is enabled")

    mcp_server = crud_mcp.get_mcp_server(db, server_id=query.mcp_server_id)
    if not mcp_server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    api_key = get_mcp_api_key(db, user_id=current_user.id, mcp_name=mcp_server.name)
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail=f"API key for {mcp_server.name} not found in user settings. Please add it via the user settings endpoint.",
        )

    # MCP query execution is delegated to Celery so API latency stays bounded.
    task = query_mcp_task.delay(mcp_server.url, api_key, query.query)
    return {"task_id": task.id}
