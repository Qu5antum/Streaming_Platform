

from .base_repository import BaseRepository
from src.database.models import StreamMetric


class StreamMetricRepository(BaseRepository):
    model = StreamMetric