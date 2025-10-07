
from pydantic import BaseModel
from typing import List, Optional
from enums import UserType

class PermissionBase(BaseModel):
    name: str

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int

    class Config:
        orm_mode = True

class PermissionGroupBase(BaseModel):
    name: str

class PermissionGroupCreate(PermissionGroupBase):
    pass

class PermissionGroup(PermissionGroupBase):
    id: int
    permissions: List[Permission] = []

    class Config:
        orm_mode = True

class ToolBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    icon_url: Optional[str] = None

class ToolCreate(ToolBase):
    pass

class Tool(ToolBase):
    id: int
    permission_group: Optional[PermissionGroup] = None

    class Config:
        orm_mode = True

class McpServerBase(BaseModel):
    name: str
    url: str
    type: str
    icon_url: Optional[str] = None

class McpServerCreate(McpServerBase):
    pass

class McpServer(McpServerBase):
    id: int
    permission_group: Optional[PermissionGroup] = None

    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    permission_groups: List[PermissionGroup] = []

    class Config:
        orm_mode = True

class UserSettingBase(BaseModel):
    key: str
    value: str

class UserSettingCreate(UserSettingBase):
    pass

class UserSetting(UserSettingBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class AppSettingBase(BaseModel):
    key: str
    value: str

class AppSettingCreate(AppSettingBase):
    isFirstRun: Optional[bool] = None

class AppSetting(AppSettingBase):
    id: int
    isFirstRun: bool

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    user_type: UserType

class User(UserBase):
    id: int
    is_active: bool
    user_type: UserType
    roles: List[Role] = []
    permission_groups: List[PermissionGroup] = []
    settings: List[UserSetting] = []

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
