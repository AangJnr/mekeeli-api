
import uuid
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enums import UserType, SenderType

# --- Attachment Schemas ---
class Attachment(BaseModel):
    id: str
    name: str
    type: str
    url: str
    metadata: Optional[Dict[str, Any]] = None

# --- Base Schemas ---
class PermissionBase(BaseModel):
    name: str

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: uuid.UUID

    class Config:
        orm_mode = True

class PermissionGroupBase(BaseModel):
    name: str

class PermissionGroupCreate(PermissionGroupBase):
    pass

class PermissionGroup(PermissionGroupBase):
    id: uuid.UUID
    permissions: List[Permission] = []

    class Config:
        orm_mode = True

class ToolBase(BaseModel):
    name: str
    key: str
    config: Dict[str, Any]
    description: Optional[str] = None
    type: str
    icon_url: Optional[str] = None

class ToolCreate(ToolBase):
    pass

class Tool(ToolBase):
    id: uuid.UUID
    permission_group: Optional[PermissionGroup] = None

    class Config:
        orm_mode = True

class McpServerBase(BaseModel):
    name: str
    key: str
    config: Dict[str, Any]
    url: str
    type: str
    icon_url: Optional[str] = None

class McpServerCreate(McpServerBase):
    pass

class McpServer(McpServerBase):
    id: uuid.UUID
    permission_group: Optional[PermissionGroup] = None

    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: uuid.UUID
    permission_groups: List[PermissionGroup] = []

    class Config:
        orm_mode = True

class UserSettingBase(BaseModel):
    key: str
    value: str

class UserSettingCreate(UserSettingBase):
    pass

class UserSetting(UserSettingBase):
    id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        orm_mode = True

class AppSettingBase(BaseModel):
    key: str
    value: str

class AppSettingCreate(AppSettingBase):
    isFirstRun: Optional[bool] = None

class AppSetting(AppSettingBase):
    id: uuid.UUID
    isFirstRun: bool

    class Config:
        orm_mode = True

# --- Chat Schemas ---
class ChatMessageBase(BaseModel):
    sender: SenderType
    content: str
    meta_data: Optional[Dict[str, Any]] = None

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: uuid.UUID
    session_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

class ChatSessionBase(BaseModel):
    title: Optional[str] = None

class ChatSessionCreate(ChatSessionBase):
    user_id: uuid.UUID
    org_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None

class ChatSession(ChatSessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    messages: List[ChatMessage] = []

    class Config:
        orm_mode = True

class ChatRequest(BaseModel):
    message: str = Field(..., description="User input or query.")
    task_id: Optional[str] = Field(None, description="Optional task reference for structured workflow.")
    tool_id: Optional[str] = Field(None, description="Optional single tool reference for a focused request.")
    session_id: Optional[str] = Field(None, description="Existing chat session id (if continuing).")
    attachments: Optional[List[Attachment]] = Field(default_factory=list, description="Optional files or documents.")
    context: Optional[Dict[str, Any]] = None
    stream: Optional[bool] = Field(True, description="Enable streaming responses.")

# --- Task Schemas ---
class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    tool_ids: Optional[List[str]] = None
    default_prompt: Optional[str] = None
    is_public: bool = False

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: uuid.UUID
    org_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

# --- Organization Schemas ---
class OrganizationBase(BaseModel):
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    subscription_plan: Optional[str] = "free"
    logo_url: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# --- User & Auth Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    user_type: UserType

class InitialAdminCreate(BaseModel):
    """
    Special schema for the initial setup, combining user and org creation.
    """
    admin_user: UserCreate
    organization: Optional[OrganizationCreate] = None

class User(UserBase):
    id: uuid.UUID
    is_active: bool
    user_type: UserType
    org_id: Optional[uuid.UUID] = None
    roles: List[Role] = []
    permission_groups: List[PermissionGroup] = []
    settings: List[UserSetting] = []
    tasks: List[Task] = []

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None

