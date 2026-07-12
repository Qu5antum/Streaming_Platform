from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class FollowResponse(BaseModel):
    streamer_id: UUID
    follower_id: UUID
    followed_at: datetime

    model_config = ConfigDict(from_attributes=True)
