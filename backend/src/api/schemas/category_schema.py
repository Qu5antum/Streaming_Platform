from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID


class CategoryCreate(BaseModel):
    title: str
    description: Optional[str] = None


class CategoryOut(CategoryCreate):
    id: UUID

    model_config = ConfigDict(from_attributes=True)