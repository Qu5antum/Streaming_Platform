from uuid import UUID
from decimal import Decimal
import logging

from src.database.db import AsyncSession
from src.repositories.stream_metric_repository import StreamMetricRepository
from src.redis.redis_service import RedisService
from src.exception_handlers.stream_exception import StreamMetricNotFoundException

logger = logging.getLogger("stream_metric")


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

    async def persist_metric(self, stream_id: UUID) -> None: 
        metric = await self.stream_metric_repo.get_stream_metric_by_stream_id(stream_id=stream_id)

        if not metric:
            logger.warning(
                "Stream metric not found",
                extra={"stream_id": stream_id}
            )

            raise StreamMetricNotFoundException("Stream metric not found")
        
        metric.total_views = int(await self.redis.get(f"stream:{stream_id}:total_views") or 0)
        metric.total_messages = int(await self.redis.get(f"stream:{stream_id}:messages") or 0)
        metric.total_donations = int(await self.redis.get(f"stream:{stream_id}:total_donations") or 0)

        metric.donation_amount = Decimal(
            await self.redis.get(f"stream:{stream_id}:donation_amount") or "0"
        )

        metric.peak_viewers = int(
            await self.redis.get(f"stream:{stream_id}:peak_viewers") or 0
        )

        metric.avg_watch_time = int(
            await self.get_avg_watch_time(stream_id)
        )

        logger.info(
            "Stream metric inserted to database",
            extra={"stream_id": stream_id}
        )

        await self.session.commit()

        keys = [
            f"stream:{stream_id}:current_viewers",
            f"stream:{stream_id}:peak_viewers",
            f"stream:{stream_id}:total_views",
            f"stream:{stream_id}:messages",
            f"stream:{stream_id}:total_donations",
            f"stream:{stream_id}:donation_amount",
            f"stream:{stream_id}:watch_time_total",
            f"stream:{stream_id}:watch_sessions",
        ]

        for key in keys:
            await self.redis.delete(key=key)

        logger.info("Keys deleted from redis", extra={"stream_id": stream_id})

    async def get_live_stream_metrics(self, stream_id: UUID) -> dict: 
        return {
            "current_viewers": int(await self.redis.get(f"stream:{stream_id}:current_viewers") or 0),
            "peak_viewers": int(await self.redis.get(f"stream:{stream_id}:peak_viewers") or 0),
            "total_views": int(await self.redis.get(f"stream:{stream_id}:total_views") or 0),
            "messages": int(await self.redis.get(f"stream:{stream_id}:messages") or 0),
            "total_donations": int(await self.redis.get(f"stream:{stream_id}:total_donations") or 0),
            "donation_amount": Decimal(
                await self.redis.get(f"stream:{stream_id}:donation_amount") or "0"
            ),
            "avg_watch_time": await self.get_avg_watch_time(stream_id),
        }
