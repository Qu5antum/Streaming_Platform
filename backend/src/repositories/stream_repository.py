from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from src.database.models import Stream, Category

class StreamRepository(BaseRepository):
    model = Stream

    async def get_stream_with_category_id(self, category_id: UUID):
        result = await self.session.execute(
            select(self.model)
            .join(self.model.categories)
            .where(Category.id == category_id)
            .options(
                selectinload(self.model.categories),
                selectinload(self.model.streamer)
            )
        )

        return result.scalars().all()
    