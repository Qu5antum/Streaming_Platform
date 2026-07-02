import logging
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from src.database.db import AsyncSession
from src.database.models import User
from src.repositories.user_repository import UserRepository
from src.api.schemas.user_schema import UserOut, UserUpdate
from src.exception_handlers.db_exception import DatabaseException
from src.exception_handlers.user_exceptions import UserNotFoundException

logger = logging.getLogger("category")

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session=self.session)


    async def get_user_profile(self, user: User) -> UserOut:
        user = await self.user_repo.get(id=user.id)

        logger.info("Succesfully user response",)

        return user

    
    async def get_users(self) -> list[UserOut]:
        users = await self.user_repo.get_all()

        logger.info("Successfully all users response")

        return users
    
    async def update_profile(self, user: User, user_update: UserUpdate) -> dict[str, str]:
        try:
            data=user_update.model_dump(
                exclude_unset=True,
                exclude_none=True
            )

            updated_user = await self.user_repo.update(
                id=user.id,
                data=data
            )
        
        except IntegrityError:
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








