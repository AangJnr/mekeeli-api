
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas
from app.db import models
from app.core import security
from app.crud import tools as crud_tools
from app.crud import tool_permissions as crud_tool_permissions
from app.db.session import SessionLocal

router = APIRouter()

def validate_tool_payload(tool_data: schemas.ToolBase, is_update: bool = False):
    if tool_data.danger_level and tool_data.danger_level not in {"low", "medium", "high"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid danger level")

    if tool_data.input_schema is not None and not isinstance(tool_data.input_schema, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="input_schema must be an object")

    if tool_data.output_schema is not None and not isinstance(tool_data.output_schema, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="output_schema must be an object")

    is_script_tool = tool_data.type == "script"
    has_script_config = tool_data.config is not None and "script" in tool_data.config

    if is_script_tool or has_script_config:
        if not tool_data.config:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tool config is required for script tools")
        script = tool_data.config.get("script")
        if not isinstance(script, str) or not script.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tool config requires a non-empty 'script'")
        entrypoint = tool_data.config.get("entrypoint", "run")
        if entrypoint is not None and not isinstance(entrypoint, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tool config entrypoint must be a string")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/tools/", response_model=schemas.Tool, dependencies=[Depends(security.get_current_admin_user)])
def create_tool(tool: schemas.ToolCreate, db: Session = Depends(get_db)):
    validate_tool_payload(tool)
    return crud_tools.create_tool(db=db, tool=tool)

@router.get("/tools/", response_model=list[schemas.Tool], dependencies=[Depends(security.get_current_admin_user)])
def read_tools(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_tools.get_tools(db, skip=skip, limit=limit)

@router.get("/tools/{tool_id}", response_model=schemas.Tool, dependencies=[Depends(security.get_current_admin_user)])
def read_tool(tool_id: str, db: Session = Depends(get_db)):
    db_tool = crud_tools.get_tool(db, tool_id=tool_id)
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return db_tool

@router.patch("/tools/{tool_id}", response_model=schemas.Tool, dependencies=[Depends(security.get_current_admin_user)])
def update_tool(tool_id: str, updates: schemas.ToolUpdate, db: Session = Depends(get_db)):
    db_tool = crud_tools.get_tool(db, tool_id=tool_id)
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    validate_tool_payload(updates, is_update=True)
    return crud_tools.update_tool(db, db_tool, updates)

@router.post("/tools/{tool_id}/enable", response_model=schemas.Tool, dependencies=[Depends(security.get_current_admin_user)])
def enable_tool(tool_id: str, db: Session = Depends(get_db)):
    db_tool = crud_tools.get_tool(db, tool_id=tool_id)
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return crud_tools.set_tool_enabled(db, db_tool, True)

@router.post("/tools/{tool_id}/disable", response_model=schemas.Tool, dependencies=[Depends(security.get_current_admin_user)])
def disable_tool(tool_id: str, db: Session = Depends(get_db)):
    db_tool = crud_tools.get_tool(db, tool_id=tool_id)
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return crud_tools.set_tool_enabled(db, db_tool, False)

@router.post("/tools/{tool_id}/permissions", response_model=schemas.ToolPermission, dependencies=[Depends(security.get_current_admin_user)])
def grant_tool_permission(
    tool_id: str,
    permission: schemas.ToolPermissionCreate,
    db: Session = Depends(get_db),
):
    if str(permission.tool_id) != str(tool_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tool ID mismatch")
    db_tool = crud_tools.get_tool(db, tool_id=tool_id)
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return crud_tool_permissions.create_tool_permission(db, permission)
