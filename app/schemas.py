
import uuid
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.enums import UserType, SenderType

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
    enabled: bool = False
    requires_network: bool = False
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    danger_level: str = "low"

class ToolCreate(ToolBase):
    pass

class Tool(ToolBase):
    id: uuid.UUID
    permission_group: Optional[PermissionGroup] = None
    permissions: Optional[List["ToolPermission"]] = None

    class Config:
        orm_mode = True

class ToolUpdate(BaseModel):
    name: Optional[str] = None
    key: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    type: Optional[str] = None
    icon_url: Optional[str] = None
    enabled: Optional[bool] = None
    requires_network: Optional[bool] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    danger_level: Optional[str] = None

class ToolPermissionBase(BaseModel):
    tool_id: uuid.UUID
    scope: str
    conversation_id: Optional[uuid.UUID] = None
    allowed: bool = True

class ToolPermissionCreate(ToolPermissionBase):
    pass

class ToolPermission(ToolPermissionBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

class ToolRunBase(BaseModel):
    tool_id: uuid.UUID
    conversation_id: Optional[uuid.UUID] = None
    status: str
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ToolRun(ToolRunBase):
    id: uuid.UUID
    started_at: datetime
    finished_at: Optional[datetime] = None

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

class SettingsBase(BaseModel):
    offline_mode: bool = True
    default_text_model: Optional[str] = None
    default_vision_model: Optional[str] = None
    default_embed_model: Optional[str] = None
    retention_days: Optional[int] = None

class SettingsUpdate(BaseModel):
    offline_mode: Optional[bool] = None
    default_text_model: Optional[str] = None
    default_vision_model: Optional[str] = None
    default_embed_model: Optional[str] = None
    retention_days: Optional[int] = None

class Settings(SettingsBase):
    id: uuid.UUID
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Diagnostics(BaseModel):
    offline_mode: bool
    external_endpoints: List[str]
    enabled_tools: List[Dict[str, Any]]
    ollama_models: List[str]
    recent_tool_runs: List[Dict[str, Any]]

# --- Files + RAG Schemas ---
class FileBase(BaseModel):
    name: str
    mime: str
    size_bytes: int
    storage_path: str
    extracted_text_path: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")

class File(FileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    org_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class RagDocument(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    file_id: uuid.UUID
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

class RagChunk(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    file_id: uuid.UUID
    chunk_index: int
    text: str
    page: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")
    created_at: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class RagQueryRequest(BaseModel):
    query: str
    top_k: int = 5

class RagQueryChunk(BaseModel):
    text: str
    file_id: uuid.UUID
    page: Optional[int] = None
    chunk_id: uuid.UUID
    score: float

class RagQueryResponse(BaseModel):
    chunks: List[RagQueryChunk]

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

class ChatSessionCreateRequest(ChatSessionBase):
    pass

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None

class ChatSession(ChatSessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    messages: List[ChatMessage] = []

    class Config:
        orm_mode = True

class ChatSessionSummary(ChatSessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

class ChatRequest(BaseModel):
    message: str = Field(..., description="User input or query.")
    task_id: Optional[str] = Field(None, description="Optional task reference for structured workflow.")
    tool_id: Optional[str] = Field(None, description="Optional single tool reference for a focused request.")
    conversation_id: Optional[str] = Field(None, description="Existing conversation id (if continuing).")
    session_id: Optional[str] = Field(None, description="Legacy session id (use conversation_id instead).")
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
    schedule_type: str = "once"
    schedule_value: Optional[str] = None
    timezone: str = "Africa/Accra"
    payload: Optional[Dict[str, Any]] = None
    enabled: bool = True

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tool_ids: Optional[List[str]] = None
    default_prompt: Optional[str] = None
    is_public: Optional[bool] = None
    schedule_type: Optional[str] = None
    schedule_value: Optional[str] = None
    timezone: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None

class Task(TaskBase):
    id: uuid.UUID
    org_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    created_at: datetime
    next_run_at: Optional[datetime] = None
    enabled: bool = Field(..., alias="is_active")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class TaskRun(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    status: str
    logs: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

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


class SetupStatus(BaseModel):
    setup_completed: bool
    setup_required: bool


class SetupBootstrapRequest(BaseModel):
    username: str = Field(..., description="Username or email for the initial admin")
    password: str


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


class SetupBootstrapResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
