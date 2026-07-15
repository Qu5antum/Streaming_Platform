from uuid import UUID
import logging
from sqlalchemy.exc import IntegrityError
import json

from src.database.db import AsyncSession
from src.database.models import User, Status
from src.api.schemas.stream_message_schema import MessageRequest, MessageResponse
from src.repositories.stream_message_repository import StreamMessageRepository
from src.repositories.stream_repository import StreamRepository
from src.exception_handlers.stream_exception import StreamNotFoundException, InvalidStreamStatusException
from src.exception_handlers.db_exception import DatabaseException
from src.services.stream_metric_serivce import StreamMetricService
from src.redis.redis_service import RedisService

logger = logging.getLogger("stream_metric")


class StreamMessageService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.stream_repo = StreamRepository(session=self.session)
        self.stream_message_repo = StreamMessageRepository(session=self.session)
        self.stream_metric_service = StreamMetricService(session=self.session)
        self.redis = redis_service

    async def add_new_message(self, stream_id: UUID, user: User, message: MessageRequest) -> MessageResponse:
        stream = await self.stream_repo.get(id=stream_id)

        if not stream:
            logger.warning(
                "Stream not found",
                extra={"stream_id": str(stream_id)}
            )

            raise StreamNotFoundException("Stream not found")
        
        if stream.status != Status.LIVE:
            logger.warning(
                "Stream status is not live",
                extra={"stream_id": str(stream_id)}
            )

            raise InvalidStreamStatusException("Stream is not live")
        
        try:
            new_message = await self.stream_message_repo.create(
                content=message.content,
                stream_id=stream_id,
                sender_id=user.id
            )

            await self.session.commit()
        
        except IntegrityError:
            await self.session.rollback()

            logger.error(
                "Message insert error, Database error",
                exc_info=True,
                extra={"stream_id": str(stream_id)}
            )

            raise DatabaseException("Database error")
        
        logger.info(
            "Stream metric service, increment messages called",
            extra={"stream_id": str(stream_id)}
        )

        await self.stream_metric_service.increment_messages(
            stream_id=stream_id
        )
        
        logger.info(
            "Message inserted in database",
            extra={"stream_id": str(stream_id)}
        )

        return new_message
    
    async def get_messages_by_stream_id(self, stream_id: UUID) -> list[MessageResponse]:
        stream = await self.stream_repo.get(id=stream_id)

        if not stream:
            logger.warning(
                "Stream not found",
                extra={"stream_id": str(stream_id)}
            )

            raise StreamNotFoundException("Stream not found")
        
        if stream.status != Status.LIVE:
            logger.warning(
                "Stream status is not live",
                extra={"stream_id": str(stream_id)}
            )

            raise InvalidStreamStatusException("Stream is not live")
        
        cached_data = await self.redis.get(f"stream:{stream_id}:messages")

        if cached_data: 
            logger.info("Messages fetched from Redis cache")

            return [
                MessageResponse.model_validate(item)
                for item in json.loads(cached_data)
            ]
        
        messages = await self.stream_message_repo.get_messages_by_stream_id(stream_id=stream_id)

        logger.info(
            "Successful response of messages by stream id",
            extra={"stream_id": str(stream_id)}
        )

        serialized = [
            MessageResponse.model_validate(message).model_dump(mode="json")
            for message in messages
        ]

        await self.redis.set(
            f"stream:{stream_id}:messages",
            json.dumps(serialized),
            expire_seconds=300
        )

        logger.info("Messages cached in Redis")

        await self.redis.delete(
            f"stream:{stream_id}:messages"
        )

        logger.info("Old key of stream messages deleted from Redis")

        return [
            MessageResponse.model_validate(message)
            for message in messages
        ]
        
            

