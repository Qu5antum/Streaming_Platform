from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class CategoryCreate(BaseModel):
    title: str
    description: Optional[str]


class CategoryOut(CategoryCreate):
    id: UUID
    
    class Config:
        from_attributes = True