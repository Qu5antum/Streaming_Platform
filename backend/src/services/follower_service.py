import logging
from uuid import UUID
from sqlalchemy.exc import IntegrityError
import json

from src.database.db import AsyncSession
from src.database.models import User
from src.repositories.follower_repository import FollowerRepository
from src.repositories.user_repository import UserRepository
from src.exception_handlers.user_exceptions import UserNotFoundException
from src.exception_handlers.db_exception import DatabaseException
from src.api.schemas.follow_schema import FollowResponse
from src.exception_handlers.follow_exception import FollowNotFoundException
from src.redis.redis_service import RedisService

logger = logging.getLogger("follower")


class FollowerService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.follower_repo = FollowerRepository(session=self.session)
        self.user_repo = UserRepository(session=self.session)
        self.redis = redis_service

    async def follow_user(self, streamer_id: UUID, user: User) -> FollowResponse:
        streamer = await self.user_repo.get(id=streamer_id)

        if not streamer:
            logger.warning(
                "Streamer not found",
                extra={"user_id", str(streamer_id)}
            )

            raise UserNotFoundException("Streamer not found")

        try:
            new_follower = await self.follower_repo.create(
                streamer_id=streamer_id,
                follower_id=user.id
            )

            await self.session.commit()
        
        except IntegrityError:
            await self.session.rollback()

            logger.error(
                "Follow user error, database error",
                exc_info=True,
                extra={
                    "streamer_id": str(streamer_id),
                    "user_id": str(user.id)
                }
            )

            raise DatabaseException("Follow user error")
        
        cache_key = f"followers:amount:{streamer_id}"

        if await self.redis.exists(cache_key):
            await self.redis.incr(cache_key)
        
        logger.info("Redis followers amount key increased")

        logger.info(
            "Successful response, user followed streamer",
            extra={
                    "streamer_id": str(streamer_id),
                    "user_id": str(user.id)
                }
        )

        return new_follower

    async def unfollow_user(self, streamer_id: UUID, user: User) -> dict[str, str]:
        streamer = await self.user_repo.get(id=streamer_id)

        if not streamer:
            logger.warning(
                "Streamer not found",
                extra={"user_id", str(streamer_id)}
            )

            raise UserNotFoundException("Streamer not found")

        follow = await self.follower_repo.get_follow_id(streamer_id=streamer_id, follower_id=user.id)

        if not follow:
            logger.warning(
                "Follow not found",
                extra={
                    "streamer_id": str(streamer_id),
                    "user_id": str(user.id)
                }
            )

            raise FollowNotFoundException("Follow not found")

        delete_follow = await self.follower_repo.delete(
            id=follow.id
        )

        if not delete_follow:
            logger.warning(
                "Follow not deleted",
                extra={"follow_id": str(follow.id)}
            )

            raise DatabaseException("Follow not deleted, Database error")
        
        cache_key = f"followers:amount:{streamer_id}"

        if await self.redis.exists(cache_key):
            await self.redis.decr(cache_key)
        
        logger.info("Redis followers amount key decreased")

        logger.info(
            "Follow successfully deleted",
            extra={"follow_id": str(follow.id)}
        )
        
        return {"detail": "Unfollowed successfully"}

    async def get_my_followers(self, user: User) -> list[FollowResponse]:
        cached_data = await self.redis.get(f"followers:list:{user.id}")

        if cached_data:
            logger.info("Followers fetched from Redis cache")

            return [
                FollowResponse.model_validate(item)
                for item in json.loads(cached_data)
            ]
        
        followers = await self.follower_repo.get_user_followers(streamer_id=user.id)

        serialized = [
            FollowResponse.model_validate(follower).model_dump(mode="json")
            for follower in followers
        ]

        await self.redis.set(
            "followers:all",
            json.dumps(serialized),
            expire_seconds=300
        )

        logger.info(
            "Successful response of streamer followers",
            extra={"streamer_id": str(user.id)}
        )

        return followers

    async def get_followers_amount(self, streamer_id: UUID) -> int:
        cached_amount = await self.redis.get(f"followers:amount:{streamer_id}")

        if cached_amount:
            logger.info(
                "Followers amount fetched to Redis cache",
                extra={"streamer_id", str(streamer_id)}
            )
            
            return int(cached_amount)
        
        followers_amount = self.follower_repo.get_user_followers_amount(streamer_id=streamer_id)

        await self.redis.set(
            f"followers:amount:{streamer_id}",
            str(followers_amount),
            expire_seconds=300
        )

        logger.info(
            "Successful response of followers amount",
            extra={"streamer_id": str(streamer_id)}
        )
        
        return followers_amount


            


        



