
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from database import Base
from enums import UserType, SenderType

# --- Association Tables ---

user_permission_groups = Table('user_permission_groups', Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('permission_group_id', String, ForeignKey('permission_groups.id'))
)

role_permission_groups = Table('role_permission_groups', Base.metadata,
    Column('role_id', String, ForeignKey('roles.id')),
    Column('permission_group_id', String, ForeignKey('permission_groups.id'))
)

permission_group_permissions = Table('permission_group_permissions', Base.metadata,
    Column('permission_group_id', String, ForeignKey('permission_groups.id')),
    Column('permission_id', String, ForeignKey('permissions.id'))
)

user_roles = Table('user_roles', Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('role_id', String, ForeignKey('roles.id'))
)


# --- Main Models ---

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    industry = Column(String, nullable=True)
    website = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    subscription_plan = Column(String, default="free")
    is_active = Column(Boolean, default=True)
    logo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    tool_ids = Column(ARRAY(String), nullable=True)
    default_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)

    creator = relationship("User", back_populates="tasks", lazy="joined")

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    user_type = Column(Enum(UserType))
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    organization = relationship("Organization")
    roles = relationship("Role", secondary=user_roles)
    permission_groups = relationship("PermissionGroup", secondary=user_permission_groups)
    settings = relationship("UserSetting", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="creator")

class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)

    permission_groups = relationship("PermissionGroup", secondary=role_permission_groups)

class PermissionGroup(Base):
    __tablename__ = "permission_groups"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)

    permissions = relationship("Permission", secondary=permission_group_permissions)
    mcp_server_id = Column(String, ForeignKey("mcp_servers.id"))
    tool_id = Column(String, ForeignKey("tools.id"))

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)

class McpServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    key = Column(String, unique=True, index=True)
    config = Column(JSONB)
    url = Column(String)
    type = Column(String, index=True)
    icon_url = Column(String, nullable=True)

    permission_group = relationship("PermissionGroup", uselist=False, backref="mcp_server")

class Tool(Base):
    __tablename__ = "tools"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    key = Column(String, unique=True, index=True)
    config = Column(JSONB)
    description = Column(String)
    type = Column(String, index=True)
    icon_url = Column(String, nullable=True)

    permission_group = relationship("PermissionGroup", uselist=False, backref="tool")

class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, index=True)
    value = Column(String)
    user_id = Column(String, ForeignKey("users.id"))

    user = relationship("User", back_populates="settings")

class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, index=True)
    value = Column(String)
    isFirstRun = Column(Boolean, default=True)

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    sender = Column(Enum(SenderType), nullable=False)
    content = Column(Text, nullable=False)
    meta_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    session = relationship("ChatSession", back_populates="messages")
