
from sqlalchemy.orm import Session
import models, schemas, security

# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Role CRUD
def get_role(db: Session, role_id: int):
    return db.query(models.Role).filter(models.Role.id == role_id).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Role).offset(skip).limit(limit).all()

def create_role(db: Session, role: schemas.RoleCreate):
    db_role = models.Role(name=role.name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

# Permission CRUD
def get_permission(db: Session, permission_id: int):
    return db.query(models.Permission).filter(models.Permission.id == permission_id).first()

def get_permissions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Permission).offset(skip).limit(limit).all()

def create_permission(db: Session, permission: schemas.PermissionCreate):
    db_permission = models.Permission(name=permission.name)
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

# McpServer CRUD
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

# Tool CRUD
def get_tool(db: Session, tool_id: int):
    return db.query(models.Tool).filter(models.Tool.id == tool_id).first()

def get_tools(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Tool).offset(skip).limit(limit).all()

def create_tool(db: Session, tool: schemas.ToolCreate):
    db_tool = models.Tool(**tool.dict())
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool

# UserSetting CRUD
def get_user_setting(db: Session, setting_id: int):
    return db.query(models.UserSetting).filter(models.UserSetting.id == setting_id).first()

def get_user_settings(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.UserSetting).filter(models.UserSetting.user_id == user_id).offset(skip).limit(limit).all()

def create_user_setting(db: Session, setting: schemas.UserSettingCreate, user_id: int):
    db_setting = models.UserSetting(**setting.dict(), user_id=user_id)
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

# AppSetting CRUD
def get_app_setting(db: Session, key: str):
    return db.query(models.AppSetting).filter(models.AppSetting.key == key).first()

def get_app_settings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AppSetting).offset(skip).limit(limit).all()

def create_app_setting(db: Session, setting: schemas.AppSettingCreate):
    db_setting = models.AppSetting(**setting.dict())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting
