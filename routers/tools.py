
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, crud, models, security
from database import SessionLocal

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/tools/", response_model=schemas.Tool, dependencies=[Depends(security.get_current_admin_user)])
def create_tool(tool: schemas.ToolCreate, db: Session = Depends(get_db)):
    return crud.create_tool(db=db, tool=tool)

@router.get("/tools/", response_model=list[schemas.Tool], dependencies=[Depends(security.get_current_admin_user)])
def read_tools(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tools = crud.get_tools(db, skip=skip, limit=limit)
    return tools

@router.get("/tools/{tool_id}", response_model=schemas.Tool, dependencies=[Depends(security.get_current_admin_user)])
def read_tool(tool_id: int, db: Session = Depends(get_db)):
    db_tool = crud.get_tool(db, tool_id=tool_id)
    if db_tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return db_tool
