
import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table, Enum
from sqlalchemy.orm import relationship
from database import Base
from enums import UserType

# Association tables for many-to-many relationships
user_permission_groups = Table('user_permission_groups', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('permission_group_id', Integer, ForeignKey('permission_groups.id'))
)

role_permission_groups = Table('role_permission_groups', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_group_id', Integer, ForeignKey('permission_groups.id'))
)

permission_group_permissions = Table('permission_group_permissions', Base.metadata,
    Column('permission_group_id', Integer, ForeignKey('permission_groups.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    user_type = Column(Enum(UserType))

    roles = relationship("Role", secondary="user_roles")
    permission_groups = relationship("PermissionGroup", secondary=user_permission_groups)
    settings = relationship("UserSetting", back_populates="user")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    permission_groups = relationship("PermissionGroup", secondary=role_permission_groups)

class PermissionGroup(Base):
    __tablename__ = "permission_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    permissions = relationship("Permission", secondary=permission_group_permissions)
    mcp_server_id = Column(Integer, ForeignKey("mcp_servers.id"))
    tool_id = Column(Integer, ForeignKey("tools.id"))

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class McpServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    url = Column(String)
    type = Column(String, index=True)
    icon_url = Column(String, nullable=True)

    permission_group = relationship("PermissionGroup", uselist=False, backref="mcp_server")
    
class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    type = Column(String, index=True)
    icon_url = Column(String, nullable=True)

    permission_group = relationship("PermissionGroup", uselist=False, backref="tool")

class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, index=True)
    value = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="settings")

class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    isFirstRun = Column(Boolean, default=True)

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender = Column(String)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
