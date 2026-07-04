from pydantic import BaseModel, EmailStr, field_validator, SecretStr, model_validator, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Self
import re

from src.database.models import UserRole

class DummyLoginRequest(BaseModel):
    role: UserRole


class UserBase(BaseModel):
    username: str
    email: EmailStr
    avatar_url: Optional[str]
    bio: Optional[str]


class UserCreate(UserBase):
    password: SecretStr
    confirm_password: SecretStr
    role: UserRole

    @field_validator("password", mode="after")
    @classmethod
    def validate_password_complexity(cls, value: SecretStr) -> SecretStr:
        raw_password = value.get_secret_value()
        
        if len(raw_password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
            
        if not re.search(r"[A-Z]", raw_password):
            raise ValueError("Password must contain at least one uppercase letter.")
            
        if not re.search(r"[a-z]", raw_password):
            raise ValueError("Password must contain at least one lowercase letter.")
            
        if not re.search(r"\d", raw_password):
            raise ValueError("Password must contain at least one digit.")
            
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_]", raw_password):
            raise ValueError("Password must contain at least one special character.")
            
        return value
    
    @model_validator(mode="after")
    def verify_password_match(self) -> Self:
        if self.password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("Passwords do not match.")
        return self


class UserOut(UserBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

    
class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    bio: str | None = None