
from sqlalchemy.orm import Session
import models, schemas

def get_mcp_server(db: Session, server_id: int):
    return db.query(models.McpServer).filter(models.McpServer.id == server_id).first()

def get_mcp_servers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.McpServer).offset(skip).limit(limit).all()

def create_mcp_server(db: Session, server: schemas.McpServerCreate):
    db_server = models.McpServer(**server.dict())
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server
