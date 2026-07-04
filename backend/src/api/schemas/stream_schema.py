from pydantic import BaseModel, ConfigDict
from src.database.models import Status
from uuid import UUID


class StreamCreate(BaseModel):
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
    category_ids: list[UUID]


class StreamOut(BaseModel):
    id: UUID
    title: str
    description: str
    status: Status
    stream_key: str
    streamer_id: UUID

    model_config = ConfigDict(from_attributes=True)