import logging
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import json
import datetime

from src.database.db import AsyncSession
from src.database.models import User, Status
from src.repositories.stream_repository import StreamRepository
from src.repositories.user_repository import UserRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.stream_metric_repository import StreamMetricRepository
from src.api.schemas.stream_schema import StreamCreate, StreamOut, PublishStream, StreamOutBase
from src.exception_handlers.stream_exception import StreamIsLiveExceptoin, StreamNotFoundException, StreamIsEndedException, StreamNotBelongToUser, StreamIsOfflineException, InvalidStreamStateException
from src.exception_handlers.category_exception import SomeCategoryNotFound, CategoryNotFoundException
from src.exception_handlers.db_exception import DatabaseException
from src.utils.secret_key import generate_stream_key
from src.redis.redis_service import RedisService
from .stream_metric_serivce import StreamMetricService

logger = logging.getLogger("category")


class StreamService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.stream_repo = StreamRepository(session=self.session)
        self.user_repo = UserRepository(session=self.session)
        self.category_repo = CategoryRepository(session=self.session)
        self.stream_metric_repo = StreamMetricRepository(session=self.session)
        self.redis = redis_service
        self.stream_metric_serivce = StreamMetricService(session=self.session)


    async def create_stream(self, user: User, stream: StreamCreate) -> StreamOut:
        user_stream = await self.user_repo.get_user_stream(user_id=user.id)

        if user_stream:
            logger.warning(
                "User already have live stream",
                extra={"user_id": str(user.id)}
            )

            raise StreamIsLiveExceptoin("You have live stream")

        categories = await self.category_repo.get_categories_with_ids(
            category_ids=stream.category_ids
        )

        if len(categories) != len(stream.category_ids):
            logger.warning("Some categories not found")

            raise SomeCategoryNotFound("Some categories not found")
        try:
            new_stream = await self.stream_repo.create(
                title = stream.title,
                description = stream.description,
                thumbnail_url = stream.thumbnail_url,
                stream_key = generate_stream_key(),
                status = Status.OFFLINE,
                streamer_id = user.id,
                categories = categories
            )

            await self.session.commit()
            await self.session.refresh(new_stream)
        except IntegrityError:
            await self.session.rollback()

            logger.error(
                "Stream not created, Database Error!",
                exc_info=True,
                extra={"stream_title": stream.title}
            )

            raise DatabaseException("Database Error!")
        
        logger.info(
            "New Stream created",
            extra={"stream_id": str(new_stream.id)}
        )
        
        return new_stream
    
    async def find_stream_by_category(self, category_id: UUID, user: User) -> list[StreamOutBase]:
        cached_data = await self.redis.get("streams:all")

        if cached_data:
            logger.info("Live Streams fetched from Redis cache")

            return [
                StreamOut.model_validate(item)
                for item in json.loads(cached_data)
            ]

        category = await self.category_repo.get(id=category_id)

        if not category:
            logger.warning(
                "Category not found",
                extra={"category_id": category_id}
            )

            raise CategoryNotFoundException("Category not found")

        streams = await self.stream_repo.get_stream_with_category_id(category_id=category_id, user=user)

        logger.info("Successful response")

        serialized = [
            StreamOut.model_validate(stream).model_dump(mode="json")
            for stream in streams
        ]

        await self.redis.set(
            "streams:all",
            json.dumps(serialized),
            expire_seconds=300
        )

        return [
            StreamOut.model_validate(stream)
            for stream in streams
        ]
    
    async def stream_detail(self, stream_id: UUID) -> StreamOutBase:
        stream = await self.stream_repo.get(id=stream_id)

        if not stream:
            logger.warning(
                "Stream not found",
                extra={"stream_id": str(stream_id)}
            )

            raise StreamNotFoundException("Live stream not found")
        
        return stream

    async def start_stream_by_stream_key(self, stream_publish: PublishStream, user: User) -> StreamOut:
        # TODO add notification for followers with redis
        stream = await self.stream_repo.get_stream_by_key(stream_key=stream_publish.stream_key)

        if not stream:
            logger.warning(
                "Stream not found by key",
                extra={"stream_key": stream_publish.stream_key}
            )

            raise StreamNotFoundException("Stream not found")
        
        if stream.streamer_id != user.id:
            logger.warning(
                "This stream does not belong to this user",
                extra={
                    "stream_key": stream_publish.stream_key,
                    "user_id": str(user.id)
                }
            )

            raise StreamNotBelongToUser("Stream not belong to user")
        
        if stream.status != Status.OFFLINE:
            logger.warning(
                "Only offline stream can go live",
                extra={"stream_id": stream.id}
            )
            
            raise InvalidStreamStateException("Only offline streams can be started")

        stream.status = Status.LIVE
        stream.started_at = datetime.datetime.now(datetime.UTC)

        await self.stream_metric_repo.create(
            stream_id = stream.id
        )

        await self.session.commit()
        await self.session.refresh(stream)

        logger.info(
            "Stream is started",
            extra={"stream_id": stream.id}
        )

        return stream

    async def stop_stream(self, stream_id: UUID, user: User) -> dict[str, str]:
        stream = await self.stream_repo.get(id=stream_id)

        if not stream:
            logger.warning(
                "Stream not found",
                extra={"stream_id": stream_id}
            )

            raise StreamNotFoundException("Stream not found")
        
        if stream.streamer_id != user.id:
            logger.warning(
                "This stream does not belong to this user",
                extra={
                    "stream_id": stream_id,
                    "user_id": str(user.id)
                }
            )

            raise StreamNotBelongToUser("Stream not belong to user")
        
        if stream.status != Status.LIVE:
            logger.warning(
                "Stream is not live, Stream cannot be ended",
                extra={"stream_id": stream_id}
            )

            raise InvalidStreamStateException("Stream must be live to end stream")
        
        stream.status = Status.ENDED
        stream.ended_at = datetime.datetime.now(datetime.UTC)

        await self.stream_metric_serivce.persist_metric(stream_id=stream.id)
        await self.session.commit()
        await self.session.refresh(stream)

        return {"detail": "Stream successfully ended"}
    
    async def delete_stream_by_id(self, stream_id: UUID) -> dict[str, str]:
        stream = await self.stream_repo.get(id=stream_id)

        if not stream:
            logger.warning(
                "Stream not found",
                extra={"stream_id": str(stream_id)}
            )

            raise StreamNotFoundException("Stream not found")
        
        try:
            await self.stream_repo.delete(id=stream_id)
        except Exception:
            logger.error(
                "Failed to delete stream",
                exc_info=True,
                extra={"stream_id": str(stream_id)}
            )

            raise DatabaseException("Stream not deleted, Database Error")

        logger.info(
            "Stream successfully deleted",
            extra={"stream_id": str(stream_id)}
        )

        return {"detail": "Stream successfully deleted"}
    
    async def get_my_streams(self, user: User) -> list[StreamOut]:
        cached_data = await self.redis.get("streams:all")

        if cached_data:
            logger.info("Streams fetched from Redis cache")

            return [
                StreamOut.model_validate(item)
                for item in json.loads(cached_data)
            ]
        
        streams = await self.stream_repo.get_user_streams(user=user)

        logger.info("Successful stream response")
        
        serialized = [
            StreamOut.model_validate(stream).model_dump(mode="json")
            for stream in streams
        ]

        await self.redis.set(
            "streams:all",
            json.dumps(serialized),
            expire_seconds=300
        )

        logger.info("Streams cached in redis")

        return [
            StreamOut.model_validate(stream)
            for stream in streams
        ]




        
        


