from sqlalchemy import select
from typing import Optional

from .base_repository import BaseRepository
from src.database.models import User


class UserRepository(BaseRepository):
    model = User

    async def get_user_with_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(self.model).where(self.model.email == email)
        )

        return result.scalar_one_or_none()