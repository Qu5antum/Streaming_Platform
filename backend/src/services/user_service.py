import logging
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import json
from typing import Any

from src.database.db import AsyncSession
from src.database.models import User
from src.repositories.user_repository import UserRepository
from src.api.schemas.user_schema import UserOut, UserUpdate
from src.exception_handlers.db_exception import DatabaseException
from src.exception_handlers.user_exceptions import UserNotFoundException
from src.redis.redis_service import RedisService

logger = logging.getLogger("user")


class UserService:
    def __init__(self, session: AsyncSession, redis_service: RedisService):
        self.session = session
        self.user_repo = UserRepository(session=self.session)
        self.redis = redis_service

    async def get_user_profile(self, user: User) -> UserOut:
        cache_key = f"user: {user.id}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            logger.info("User fetched from Redis cache")

            return UserOut.model_validate(json.loads(cached_data))
        
        user = await self.user_repo.get(id=user.id)

        logger.info("Succesfully user response")

        user_schema = UserOut.model_validate(user)

        await self.redis.set(
            "user:one",
            json.dumps(user_schema.model_dump(mode="json")),
            expire_seconds=300
        )

        logger.info("User cached in Redis")

        return user_schema
    
    # TODO Implement redis service
    async def get_users(self) -> list[UserOut]:
        users = await self.user_repo.get_all()

        logger.info("Successfully all users response")

        return users
    
    async def search_user(self, username: str) -> list[dict[Any, UserOut]]:
        users = await self.user_repo.search_user_by_username(username=username)

        return users
    
    async def update_profile(self, user: User, user_update: UserUpdate) -> dict[str, str]:
        try:
            data = user_update.model_dump(
                exclude_unset=True,
                exclude_none=True
            )

            updated_user = await self.user_repo.update(
                id=user.id,
                data=data
            )
        
        except IntegrityError:
            await self.session.rollback()
            
            logger.error(
                "User not updated, database integrity error",
                exc_info=True,
                extra={"username": user_update.username}
            )
            raise DatabaseException("Integrity constraint violation")

        logger.info(
            "User successfully updated",
            extra={"username": updated_user.username}
        )

        return {"detail": "Profile updated"}

    async def delete_user(self, user_id: UUID) -> dict[str, str]:
        user = await self.user_repo.get(id=user_id)

        if not user:
            logger.warning(
                "User not found",
                extra={"user_id": user_id}
            )

            raise UserNotFoundException("User not found")
        
        await self.user_repo.delete(id=user_id)

        logger.info(
            "User deleted successfuly",
            extra={"user_id": user_id}
        )

        return {"detail": "User successfully deleted"}








