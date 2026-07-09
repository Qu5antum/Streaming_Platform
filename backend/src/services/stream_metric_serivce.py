from uuid import UUID

from src.database.db import AsyncSession
from src.database.models import User
from src.repositories.stream_metric_repository import StreamMetricRepository
from src.redis.redis_service import RedisService


class StreamMetricService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.redis = redis_service
        self.stream_metric_repo = StreamMetricRepository(session=self.session)

    async def register_view(self, stream_id: UUID, user: User):
        pass