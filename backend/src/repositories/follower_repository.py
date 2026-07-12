from sqlalchemy import select

from .base_repository import BaseRepository
from src.database.models import Follower


class FollowerRepository(BaseRepository):
    model = Follower

    async def get_follow_id(self, streamer_id: UUID, follower_id: UUID):
        result = await self.session.execute(
            select(self.model.id)
            .where(
                self.model.streamer_id == streamer_id,
                self.model.follower_id == follower_id
            )
        )

        return result.scalar_one_or_none()