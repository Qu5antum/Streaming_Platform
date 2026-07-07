from pydantic import BaseModel, ConfigDict
from src.database.models import Status
from uuid import UUID


class StreamCreate(BaseModel):
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
    category_ids: list[UUID]


class StreamOutBase(BaseModel):
    id: UUID
    title: str
    description: str
    status: Status
    streamer_id: UUID

    model_config = ConfigDict(from_attributes=True)


class StreamOut(StreamOutBase):
    stream_key: str


    model_config = ConfigDict(from_attributes=True)




class PublishStream(BaseModel):
    stream_key: str