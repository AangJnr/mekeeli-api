
from sqlalchemy.orm import Session
import models, schemas
from . import permissions as crud_permissions
from . import permission_groups as crud_permission_groups

def get_mcp_server(db: Session, server_id: int):
    return db.query(models.McpServer).filter(models.McpServer.id == server_id).first()

def get_mcp_servers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.McpServer).offset(skip).limit(limit).all()

def create_mcp_server(db: Session, server: schemas.McpServerCreate):
    # 1. Create the MCP Server
    db_server = models.McpServer(**server.dict())
    db.add(db_server)
    db.commit()
    db.refresh(db_server)

    # 2. Auto-generate a permission group for this MCP
    pg_name = f"MCP-{db_server.name}-Permissions"
    db_permission_group = crud_permission_groups.create_permission_group(
        db, schemas.PermissionGroupCreate(name=pg_name)
    )

    # 3. Associate the permission group with the MCP
    db_server.permission_group_id = db_permission_group.id
    db.commit()
    
    # 4. Create standard CRUD permissions for this MCP
    permissions_to_create = ["read", "update", "delete"]
    for p_name in permissions_to_create:
        full_permission_name = f"mcp:{db_server.name}:{p_name}"
        db_permission = crud_permissions.create_permission(
            db, schemas.PermissionCreate(name=full_permission_name)
        )
        # 5. Add the new permission to the group
        crud_permission_groups.add_permission_to_group(db, db_permission_group, db_permission)

    db.refresh(db_server)
    return db_server

def edit_mcp_server(db: Session, server_id: int, server_update: schemas.McpServerCreate):
    db_server = get_mcp_server(db, server_id)
    if not db_server:
        return None
    for key, value in server_update.dict().items():
        setattr(db_server, key, value)
    db.commit()
    db.refresh(db_server)
    return db_server
