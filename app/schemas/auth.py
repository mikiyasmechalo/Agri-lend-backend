from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role_name: str
    phone_number: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role_id: UUID
    is_active: bool
    locale: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]

    model_config = {"from_attributes": True}
