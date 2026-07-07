from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from src.database.models import Stream, Category, User, UserRole, Status

class StreamRepository(BaseRepository):
    model = Stream

    async def get_stream_with_category_id(self, category_id: UUID, user: User):
        if user.role == UserRole.USER:
            status = Status.LIVE
        else:
            status = Status.OFFLINE

        query = (
            select(self.model)
            .join(self.model.categories)
            .where(
                Category.id == category_id,
                self.model.status == status
            )
            .options(
                selectinload(self.model.categories),
                selectinload(self.model.streamer)
            )
        )

        result = await self.session.execute(query)

        return result.scalars().all()
    
    async def get_stream_by_key(self, stream_key: str):
        result = await self.session.execute(
            select(self.model)
            .where(
                self.model.stream_key == stream_key,
                self.model.status == Status.OFFLINE

            )
        )

        return result.scalar_one_or_none()
    
    async def get_user_streams(self, user: User):
        result = await self.session.execute(
            select(self.model)
            .where(self.model.streamer_id == user.id)
        )

        return result.scalars().all()   

    