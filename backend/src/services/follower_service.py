import logging
from uuid import UUID
from sqlalchemy.exc import IntegrityError

from src.database.db import AsyncSession
from src.database.models import User
from src.repositories.follower_repository import FollowerRepository
from src.repositories.user_repository import UserRepository
from src.exception_handlers.user_exceptions import UserNotFoundException
from src.exception_handlers.db_exception import DatabaseException
from src.api.schemas.follow_schema import FollowResponse
from src.exception_handlers.follow_exception import FollowNotFoundException

logger = logging.getLogger("follower")


class FollowerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.follower_repo = FollowerRepository(session=self.session)
        self.user_repo = UserRepository(session=self.session)

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
        
        logger.info(
            "Follow successfully deleted",
            extra={"follow_id": str(follow.id)}
        )
        
        return {"detail": "Unfollowed successfully"}

    async def get_my_followers(self, user: User) -> list[FollowResponse]:
        # Todo implement redis service
        followers = await self.follower_repo.get_user_followers(streamer_id=user.id)

        logger.info(
            "Successful response of streamer followers",
            extra={"streamer_id": str(user.id)}
        )

        return followers

    async def get_followers_amount(self, streamer_id: UUID) -> int:
        # Todo implement redis service
        followers_amount = self.follower_repo.get_user_followers_amount(streamer_id=streamer_id)

        logger.info(
            "Successful response of followers amount",
            extra={"streamer_id": str(streamer_id)}
        )
        
        return followers_amount


            


        



