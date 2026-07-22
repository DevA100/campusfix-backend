"""
Pydantic schemas for user registration, output, and role information.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class RoleOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone_number: Optional[str] = None
    department: Optional[str] = None
    role_name: str = Field(
        ...,
        description="Role: STUDENT, STAFF, MAINTENANCE_OFFICER, or ADMIN (case-insensitive)"
    )


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone_number: Optional[str]
    department: Optional[str]
    is_active: bool
    role: RoleOut
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    role_name: Optional[str] = None
