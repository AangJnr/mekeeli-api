
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

@router.post("/mcp_servers/", response_model=schemas.McpServer, dependencies=[Depends(security.get_current_admin_user)])
def create_mcp_server(server: schemas.McpServerCreate, db: Session = Depends(get_db)):
    return crud.create_mcp_server(db=db, server=server)

@router.get("/mcp_servers/", response_model=list[schemas.McpServer], dependencies=[Depends(security.get_current_admin_user)])
def read_mcp_servers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    servers = crud.get_mcp_servers(db, skip=skip, limit=limit)
    return servers

@router.get("/mcp_servers/{server_id}", response_model=schemas.McpServer, dependencies=[Depends(security.get_current_admin_user)])
def read_mcp_server(server_id: int, db: Session = Depends(get_db)):
    db_server = crud.get_mcp_server(db, server_id=server_id)
    if db_server is None:
        raise HTTPException(status_code=404, detail="McpServer not found")
    return db_server
