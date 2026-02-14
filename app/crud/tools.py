
from sqlalchemy.orm import Session
from app.db import models
from app import schemas
from . import permissions as crud_permissions
from . import permission_groups as crud_permission_groups

def get_tool(db: Session, tool_id: str):
    return db.query(models.Tool).filter(models.Tool.id == tool_id).first()

def get_tools(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Tool).offset(skip).limit(limit).all()

def create_tool(db: Session, tool: schemas.ToolCreate):
    # 1. Create the Tool
    db_tool = models.Tool(**tool.dict())
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)

    # 2. Auto-generate a permission group for this Tool
    pg_name = f"Tool-{db_tool.name}-Permissions"
    db_permission_group = crud_permission_groups.create_permission_group(
        db, schemas.PermissionGroupCreate(name=pg_name)
    )

    # 3. Associate the permission group with the Tool
    db_tool.permission_group_id = db_permission_group.id
    db.commit()

    # 4. Create standard CRUD permissions for this Tool
    permissions_to_create = ["use", "edit"]
    for p_name in permissions_to_create:
        full_permission_name = f"tool:{db_tool.name}:{p_name}"
        db_permission = crud_permissions.create_permission(
            db, schemas.PermissionCreate(name=full_permission_name)
        )
        # 5. Add the new permission to the group
        crud_permission_groups.add_permission_to_group(db, db_permission_group, db_permission)

    db.refresh(db_tool)
    return db_tool

def update_tool(db: Session, tool: models.Tool, updates: schemas.ToolUpdate):
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tool, key, value)
    db.commit()
    db.refresh(tool)
    return tool

def set_tool_enabled(db: Session, tool: models.Tool, enabled: bool):
    tool.enabled = enabled
    db.commit()
    db.refresh(tool)
    return tool
