from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

from src.database.models import UserRole

class DummyLoginRequest(BaseModel):
    role: UserRole


class UserBase(BaseModel):
    username: str
    email: EmailStr
    avatar_url: Optional[str]
    bio: Optional[str]


class UserCreate(UserBase):
    password: str
    role: UserRole


class UserOut(UserBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True