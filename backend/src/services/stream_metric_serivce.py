from uuid import UUID
from decimal import Decimal

from src.database.db import AsyncSession
from src.database.models import User
from src.repositories.stream_metric_repository import StreamMetricRepository
from src.redis.redis_service import RedisService


class StreamMetricService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.redis = redis_service
        self.stream_metric_repo = StreamMetricRepository(session=self.session)

    async def viewer_connected(self, stream_id: UUID):
        current_viewers_key = f"stream:{stream_id}:current_viewers"
        peak_key = f"stream:{stream_id}:peak_viewers"

        current_viewers = await self.redis.incr(key=current_viewers_key)

        peak = await self.redis.get(key=peak_key)

        if peak is None or current_viewers > int(peak):
            await self.redis.set(
                peak_key,
                current_viewers
            )

    async def viewer_discconnected(self, stream_id: UUID):
        current_viewers_key = f"stream:{stream_id}:current_viewers"

        current_viewers = await self.redis.decr(key=current_viewers_key)

        if current_viewers < 0:
            await self.redis.set(current_viewers_key, "0")

    async def register_view(self, stream_id: UUID):
        total_views_key = f"stream:{stream_id}:total_views"

        await self.redis.incr(key=total_views_key)

    async def increment_messages(self, stream_id: UUID):
        messages_key = f"stream:{stream_id}:messages"

        await self.redis.incr(key=messages_key)

    async def register_donation(self, stream_id: UUID, amount: Decimal):
        total_donations_key = f"stream:{stream_id}:total_donations"
        donation_amount_key = f"stream:{stream_id}:donation_amount"
        
        await self.redis.incr(key=total_donations_key)
        await self.redis.incrbyfloat(key=donation_amount_key, amount=float(amount))

    async def register_watch_session(self, stream_id: UUID, seconds_watched: int):
        watch_time_key = f"stream:{stream_id}:watch_time_total"
        watch_sessions_key = f"stream:{stream_id}:watch_sessions"

        await self.redis.incrby(key=watch_time_key, amount=seconds_watched)
        await self.redis.incr(key=watch_sessions_key)

    async def get_avg_watch_time(self, stream_id: UUID) -> float:
        watch_time_key = f"stream:{stream_id}:watch_time_total"
        watch_sessions_key = f"stream:{stream_id}:watch_sessions"

        total_time_str = await self.redis.get(key=watch_time_key)
        total_sessions_str = await self.redis.get(key=watch_sessions_key)

        total_time = int(total_time_str) if total_time_str else 0
        total_sessions = int(total_sessions_str) if total_sessions_str else 0

        if total_sessions == 0:
            return 0.0

        return round(total_time / total_sessions, 2)

