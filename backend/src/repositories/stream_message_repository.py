from sqlalchemy import select
from uuid import UUID

from .base_repository import BaseRepository
from src.database.models import StreamMessage


class StreamMessageRepository(BaseRepository):
    model = StreamMessage

    async def get_messages_by_stream_id(self, stream_id: UUID): 
        result = await self.session.execute(
            select(self.model)
            .where(self.model.stream_id == stream_id)
        )

        return result.scalars().all()