from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role_name: str
    phone_number: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    locale: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role_id: UUID
    is_active: bool
    locale: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role_name: str
    is_active: bool
    locale: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleAssignment(BaseModel):
    role_name: str


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]

    model_config = {"from_attributes": True}
