from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    username: str
    display_name: str
    role_id: str
    role_name: str
    permissions: List[str]
    is_superuser: bool


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=72)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=72)
    display_name: str = Field(..., min_length=1, max_length=100)
    role_id: str = Field(..., min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    status: UserStatus = UserStatus.ACTIVE


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    status: Optional[UserStatus] = None


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str
    role_id: str
    role_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    is_superuser: bool
    last_login: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int


class UserFilter(BaseModel):
    status: Optional[UserStatus] = None
    role_id: Optional[str] = None
    search: Optional[str] = None


class RoleCreate(BaseModel):
    role_id: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    permissions: List[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    permissions: Optional[List[str]] = None


class RoleResponse(BaseModel):
    id: str
    role_id: str
    name: str
    description: str
    permissions: List[str]
    is_system: bool
    created_at: datetime
    updated_at: datetime


class RoleListResponse(BaseModel):
    items: List[RoleResponse]
    total: int
    page: int
    page_size: int


class PermissionResponse(BaseModel):
    permissions: List[str]
