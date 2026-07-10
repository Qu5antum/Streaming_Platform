from uuid import UUID
from sqlalchemy import select

from .base_repository import BaseRepository
from src.database.models import StreamMetric


class StreamMetricRepository(BaseRepository):
    model = StreamMetric

    async def get_stream_metric_by_stream_id(self, stream_id: UUID):
        result = await self.session.execute(
            select(self.model)
            .where(self.model.stream_id == stream_id)
        )

        return result.scalar_one_or_none()