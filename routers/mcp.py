
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud, models, security
from database import get_db
from celery_worker import query_mcp_task
from mcp_integration import get_mcp_api_key

router = APIRouter()

class McpQuery(schemas.BaseModel):
    mcp_server_id: int
    query: str

@router.post("/mcp/query", status_code=202)
def query_mcp(
    query: McpQuery,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
):
    mcp_server = crud.get_mcp_server(db, server_id=query.mcp_server_id)
    if not mcp_server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    api_key = get_mcp_api_key(db, user_id=current_user.id, mcp_name=mcp_server.name)
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail=f"API key for {mcp_server.name} not found in user settings. Please add it via the user settings endpoint.",
        )

    task = query_mcp_task.delay(mcp_server.url, api_key, query.query)
    return {"task_id": task.id}
