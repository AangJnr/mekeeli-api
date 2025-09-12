
from pydantic import BaseModel
from typing import List, Optional

class ToolBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str

class ToolCreate(ToolBase):
    pass

class Tool(ToolBase):
    id: int

    class Config:
        orm_mode = True

class McpServerBase(BaseModel):
    name: str
    url: str
    type: str

class McpServerCreate(McpServerBase):
    pass

class McpServer(McpServerBase):
    id: int

    class Config:
        orm_mode = True

class PermissionBase(BaseModel):
    name: str

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int

    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    permissions: List[Permission] = []

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
    pass

class AppSetting(AppSettingBase):
    id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    roles: List[Role] = []
    settings: List[UserSetting] = []

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
