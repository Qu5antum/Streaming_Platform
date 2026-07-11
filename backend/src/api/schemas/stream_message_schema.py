from pydantic import BaseModel, ConfigDict
from uuid import UUID


class MessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    content: str
    sender_id: UUID
    stream_id: UUID

    model_config = ConfigDict(from_attributes=True)